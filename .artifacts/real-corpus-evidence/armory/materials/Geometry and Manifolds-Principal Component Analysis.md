[[geometry-manifolds.base]]

> Source: [[Principal Component Analysis]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/d260f3f0eec3d2e020a4913d8571d8c3e815a4cf.png]]
PCA of a [multivariate Gaussian distribution](https://en.wikipedia.org/wiki/Multivariate_Gaussian_distribution) centered at (1, 3) with a standard deviation of 3 in roughly the (0.866, 0.5) direction and of 1 in the orthogonal direction. The vectors shown are the [[Eigenvalues and Eigenvectors|eigenvectors]] of the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) scaled by the square root of the corresponding eigenvalue, and shifted so their tails are at the mean.

**Principal component analysis** (**PCA**) is a [linear](https://en.wikipedia.org/wiki/Linear_map) [dimensionality reduction](https://en.wikipedia.org/wiki/Dimensionality_reduction) technique with applications in [exploratory data analysis](https://en.wikipedia.org/wiki/Exploratory_data_analysis), visualization and [data preprocessing](https://en.wikipedia.org/wiki/Data_preprocessing).

The data are [linearly transformed](https://en.wikipedia.org/wiki/Linear_map) onto a new [coordinate system](https://en.wikipedia.org/wiki/Coordinate_system) such that the directions (principal components) capturing the largest variation in the data can be easily identified.

The **principal components** of a collection of points in a [real coordinate space](https://en.wikipedia.org/wiki/Real_coordinate_space) are a sequence of $p$ [unit vectors](https://en.wikipedia.org/wiki/Unit_vector), where the $i$-th vector is the direction of a line that best fits the data while being [orthogonal](https://en.wikipedia.org/wiki/Orthogonal) to the first $i-1$ vectors. Here, a best-fitting line is defined as one that minimizes the average squared [perpendicular](https://en.wikipedia.org/wiki/Perpendicular_distance) [distance from the points to the line](https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line). These directions (i.e., principal components) constitute an [orthonormal basis](https://en.wikipedia.org/wiki/Orthonormal_basis) in which different individual dimensions of the data are [linearly uncorrelated](https://en.wikipedia.org/wiki/Linear_correlation). Many studies use the first two principal components in order to plot the data in two dimensions and to visually identify clusters of closely related data points.

Principal component analysis has applications in many fields such as [population genetics](https://en.wikipedia.org/wiki/Population_genetics), [microbiome](https://en.wikipedia.org/wiki/Microbiome) studies, and [atmospheric science](https://en.wikipedia.org/wiki/Atmospheric_science).

## Overview

When performing PCA, the first principal component of a set of $p$ variables is the derived variable formed as a linear combination of the original variables that explains the most variance. The second principal component explains the most variance in what is left once the effect of the first component is removed, and we may proceed through $p$ iterations until all the variance is explained. PCA is most commonly used when many of the variables are highly correlated with each other and it is desirable to reduce their number to an [[Linear Independence|independent set]]. The first principal component can equivalently be defined as a direction that maximizes the variance of the projected data. The $i$-th principal component can be taken as a direction orthogonal to the first $i-1$ principal components that maximizes the variance of the projected data.

For either objective, it can be shown that the principal components are [eigenvectors](https://en.wikipedia.org/wiki/Eigenvectors) of the data's [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix). Thus, the principal components are often computed by [eigendecomposition](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix) of the data covariance matrix or [[Singular Value Decomposition]] of the data matrix. PCA is the simplest of the true eigenvector-based multivariate analyses and is closely related to [factor analysis](https://en.wikipedia.org/wiki/Factor_analysis). Factor analysis typically incorporates more domain-specific assumptions about the underlying structure and solves eigenvectors of a slightly different matrix. PCA is also related to [canonical correlation analysis (CCA)](https://en.wikipedia.org/wiki/Canonical_correlation). CCA defines coordinate systems that optimally describe the [cross-covariance](https://en.wikipedia.org/wiki/Cross-covariance) between two datasets while PCA defines a new [orthogonal coordinate system](https://en.wikipedia.org/wiki/Orthogonal_coordinate_system) that optimally describes variance in a single dataset. [Robust](https://en.wikipedia.org/wiki/Robust_principal_component_analysis) and [L1-norm](https://en.wikipedia.org/wiki/Lp_space)-based variants of standard PCA have also been proposed.

## History

PCA was invented in 1901 by [Karl Pearson](https://en.wikipedia.org/wiki/Karl_Pearson), as an analogue of the [principal axis theorem](https://en.wikipedia.org/wiki/Principal_axis_theorem) in mechanics; it was later independently developed and named by [Harold Hotelling](https://en.wikipedia.org/wiki/Harold_Hotelling) in the 1930s. Depending on the field of application, it is also named the discrete [Karhunen–Loève](https://en.wikipedia.org/wiki/Karhunen%E2%80%93Lo%C3%A8ve_theorem) transform (KLT) in [signal processing](https://en.wikipedia.org/wiki/Signal_processing), the [Hotelling](https://en.wikipedia.org/wiki/Harold_Hotelling) transform in multivariate quality control, [proper orthogonal decomposition](https://en.wikipedia.org/wiki/Proper_orthogonal_decomposition) (POD) in mechanical engineering, [[Singular Value Decomposition]] (SVD) of **X** (invented in the last quarter of the 19th century), [[Eigendecomposition|eigenvalue decomposition]] (EVD) of **X**<sup>T</sup>**X** in linear algebra, [factor analysis](https://en.wikipedia.org/wiki/Factor_analysis) (for a discussion of the differences between PCA and factor analysis see Ch. 7 of Jolliffe's *Principal Component Analysis*), [Eckart–Young theorem](https://en.wikipedia.org/wiki/Eckart%E2%80%93Young_theorem) (Harman, 1960), or [empirical orthogonal functions](https://en.wikipedia.org/wiki/Empirical_orthogonal_functions) (EOF) in meteorological science (Lorenz, 1956), empirical eigenfunction decomposition (Sirovich, 1987), quasiharmonic modes (Brooks et al., 1988), [[Spectral Theorem|spectral decomposition]] in noise and vibration, and [empirical modal analysis](https://en.wikipedia.org/wiki/Mode_shape) in structural dynamics.

## Intuition

![[media/c60adb16cd54c3b527058e2881dae056bed8896d.jpg]]
A scree plot that is meant to help interpret the PCA and decide how many components to retain. The start of the bend in the line (point of inflexion or "knee") should indicate how many components are retained, hence in this example, three factors should be retained.

PCA can be thought of as fitting a *p*-dimensional [ellipsoid](https://en.wikipedia.org/wiki/Ellipsoid) to the data, where each axis of the ellipsoid represents a principal component. If some axis of the ellipsoid is small, then the variance along that axis is also small.

To find the axes of the ellipsoid, we must first center the values of each variable in the dataset on 0 by subtracting the mean of the variable's observed values from each of those values. These transformed values are used instead of the original observed values for each of the variables. Then, we compute the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) of the data and calculate the eigenvalues and corresponding eigenvectors of this covariance matrix. Then we must [normalize](https://en.wikipedia.org/wiki/Normalization_(statistics) "Normalization (statistics)") each of the orthogonal eigenvectors to turn them into unit vectors. Once this is done, each of the mutually-orthogonal unit eigenvectors can be interpreted as an axis of the ellipsoid fitted to the data. This choice of basis will transform the covariance matrix into a diagonalized form, in which the diagonal elements represent the variance of each axis. The proportion of the variance that each eigenvector represents can be calculated by dividing the eigenvalue corresponding to that eigenvector by the sum of all eigenvalues.

[Biplots](https://en.wikipedia.org/wiki/Biplot) and [scree plots](https://en.wikipedia.org/wiki/Scree_plot) (degree of [explained variance](https://en.wikipedia.org/wiki/Explained_variance)) are used to interpret findings of the PCA.

## Details

PCA is defined as an [orthogonal](https://en.wikipedia.org/wiki/Orthogonal_transformation) [[Linear Transformation]] on a real [inner product space](https://en.wikipedia.org/wiki/Inner_product_space) that transforms the data to a new [coordinate system](https://en.wikipedia.org/wiki/Coordinate_system) such that the greatest variance by some scalar projection of the data comes to lie on the first coordinate (called the first principal component), the second greatest variance on the second coordinate, and so on.

Consider an $n\times p$ data [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)"), **X**, with column-wise zero [empirical mean](https://en.wikipedia.org/wiki/Empirical_mean) (the sample mean of each column has been shifted to zero), where each of the *n* rows represents a different repetition of the experiment, and each of the *p* columns gives a particular kind of feature (say, the results from a particular sensor).

Mathematically, the transformation is defined by a set of size $l$ (where $l$ is usually selected to be strictly less than $p$ to reduce dimensionality) of $p$-dimensional vectors of weights or coefficients $\mathbf {w} _{(k)}=(w_{1},\dots ,w_{p})_{(k)}$ that map each row vector $\mathbf {x} _{(i)}=(x_{1},\dots ,x_{p})_{(i)}$ of **X** to a new vector of principal component *scores* $\mathbf {t} _{(i)}=(t_{1},\dots ,t_{l})_{(i)}$, given by

${t_{k}}_{(i)}=\mathbf {x} _{(i)}\cdot \mathbf {w} _{(k)}\qquad \mathrm {for} \qquad i=1,\dots ,n\qquad k=1,\dots ,l$

in such a way that the individual variables $t_{1},\dots ,t_{l}$ of **t** considered over the data set successively inherit the maximum possible variance from **X**, with each coefficient vector **w** constrained to be a [unit vector](https://en.wikipedia.org/wiki/Unit_vector).

The above may equivalently be written in matrix form as

$\mathbf {T} =\mathbf {X} \mathbf {W}$

where ${\mathbf {T} }_{ik}={t_{k}}_{(i)}$, ${\mathbf {X} }_{ij}={x_{j}}_{(i)}$, and ${\mathbf {W} }_{jk}={w_{j}}_{(k)}$.

### First component

In order to maximize variance, the first weight vector **w**<sub>(1)</sub> thus has to satisfy

$\mathbf {w} _{(1)}=\arg \max _{\Vert \mathbf {w} \Vert =1}\,\left\{\sum _{i}(t_{1})_{(i)}^{2}\right\}=\arg \max _{\Vert \mathbf {w} \Vert =1}\,\left\{\sum _{i}\left(\mathbf {x} _{(i)}\cdot \mathbf {w} \right)^{2}\right\}$

Equivalently, writing this in matrix form gives

$\mathbf {w} _{(1)}=\arg \max _{\left\|\mathbf {w} \right\|=1}\left\{\left\|\mathbf {Xw} \right\|^{2}\right\}=\arg \max _{\left\|\mathbf {w} \right\|=1}\left\{\mathbf {w} ^{\mathsf {T}}\mathbf {X} ^{\mathsf {T}}\mathbf {Xw} \right\}$

Since **w**<sub>(1)</sub> has been defined to be a unit vector, it equivalently also satisfies

$\mathbf {w} _{(1)}=\arg \max \left\{{\frac {\mathbf {w} ^{\mathsf {T}}\mathbf {X} ^{\mathsf {T}}\mathbf {Xw} }{\mathbf {w} ^{\mathsf {T}}\mathbf {w} }}\right\}$

The quantity to be maximised can be recognised as a [Rayleigh quotient](https://en.wikipedia.org/wiki/Rayleigh_quotient). A standard result for a [positive semidefinite matrix](https://en.wikipedia.org/wiki/Positive_semidefinite_matrix) such as **X**<sup>T</sup>**X** is that the quotient's maximum possible value is the largest [eigenvalue](https://en.wikipedia.org/wiki/Eigenvalue) of the matrix, which occurs when ***w*** is the corresponding [eigenvector](https://en.wikipedia.org/wiki/Eigenvector).

With **w**<sub>(1)</sub> found, the first principal component of a data vector **x**<sub>(*i*)</sub> can then be given as a score *t*<sub>1(*i*)</sub> = **x**<sub>(*i*)</sub> ⋅ **w**<sub>(1)</sub> in the transformed co-ordinates, or as the corresponding vector in the original variables, {**x**<sub>(*i*)</sub> ⋅ **w**<sub>(1)</sub>} **w**<sub>(1)</sub>.

### Further components

The *k*-th component can be found by subtracting the first *k* − 1 principal components from **X**:

$\mathbf {\hat {X}} _{k}=\mathbf {X} -\sum _{s=1}^{k-1}\mathbf {X} \mathbf {w} _{(s)}\mathbf {w} _{(s)}^{\mathsf {T}}$

and then finding the weight vector which extracts the maximum variance from this new data matrix

$\mathbf {w} _{(k)}=\mathop {\operatorname {arg\,max} } _{\left\|\mathbf {w} \right\|=1}\left\{\left\|\mathbf {\hat {X}} _{k}\mathbf {w} \right\|^{2}\right\}=\arg \max \left\{{\tfrac {\mathbf {w} ^{\mathsf {T}}\mathbf {\hat {X}} _{k}^{\mathsf {T}}\mathbf {\hat {X}} _{k}\mathbf {w} }{\mathbf {w} ^{T}\mathbf {w} }}\right\}$

It turns out that this gives the remaining eigenvectors of **X**<sup>T</sup>**X**, with the maximum values for the quantity in brackets given by their corresponding eigenvalues. Thus the weight vectors are eigenvectors of **X**<sup>T</sup>**X**.

The *k*-th principal component of a data vector **x**<sub>(*i*)</sub> can therefore be given as a score *t*<sub>*k*(*i*)</sub> = **x**<sub>(*i*)</sub> ⋅ **w**<sub>(*k*)</sub> in the transformed coordinates, or as the corresponding vector in the space of the original variables, {**x**<sub>(*i*)</sub> ⋅ **w**<sub>(*k*)</sub>} **w**<sub>(*k*)</sub>, where **w**<sub>(*k*)</sub> is the *k*th eigenvector of **X**<sup>T</sup>**X**.

The full principal components decomposition of **X** can therefore be given as

$\mathbf {T} =\mathbf {X} \mathbf {W}$

where **W** is a *p*-by-*p* matrix of weights whose columns are the eigenvectors of **X**<sup>T</sup>**X**. The transpose of **W** is sometimes called the [whitening or sphering transformation](https://en.wikipedia.org/wiki/Whitening_transformation). Columns of **W** multiplied by the square root of corresponding eigenvalues, that is, eigenvectors scaled up by the variances, are called *loadings* in PCA or in Factor analysis.

### Covariances

**X**<sup>T</sup>**X** itself can be recognized as proportional to the empirical sample [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) of the dataset **X<sup>T</sup>**.

The sample covariance *Q* between two of the different principal components over the dataset is given by:

${\begin{aligned}Q(\mathrm {PC} _{(j)},\mathrm {PC} _{(k)})&\propto (\mathbf {X} \mathbf {w} _{(j)})^{\mathsf {T}}(\mathbf {X} \mathbf {w} _{(k)})\\&=\mathbf {w} _{(j)}^{\mathsf {T}}\mathbf {X} ^{\mathsf {T}}\mathbf {X} \mathbf {w} _{(k)}\\&=\mathbf {w} _{(j)}^{\mathsf {T}}\lambda _{(k)}\mathbf {w} _{(k)}\\&=\lambda _{(k)}\mathbf {w} _{(j)}^{\mathsf {T}}\mathbf {w} _{(k)}\end{aligned}}$

where the eigenvalue property of **w**<sub>(*k*)</sub> has been used to move from line 2 to line 3. However eigenvectors **w**<sub>(*j*)</sub> and **w**<sub>(*k*)</sub> corresponding to eigenvalues of a symmetric matrix are orthogonal (if the eigenvalues are different), or can be orthogonalised (if the vectors happen to share an equal repeated value). The product in the final line is therefore zero; there is no sample covariance between different principal components over the dataset.

Another way to characterise the principal components transformation is therefore as the transformation to coordinates which diagonalise the empirical sample covariance matrix.

In matrix form, the empirical covariance matrix for the original variables can be written

$\mathbf {Q} \propto \mathbf {X} ^{\mathsf {T}}\mathbf {X} =\mathbf {W} \mathbf {\Lambda } \mathbf {W} ^{\mathsf {T}}$

The empirical covariance matrix between the principal components becomes

$\mathbf {W} ^{\mathsf {T}}\mathbf {Q} \mathbf {W} \propto \mathbf {W} ^{\mathsf {T}}\mathbf {W} \,\mathbf {\Lambda } \,\mathbf {W} ^{\mathsf {T}}\mathbf {W} =\mathbf {\Lambda }$

where **Λ** is the diagonal matrix of eigenvalues *λ*<sub>(*k*)</sub> of **X**<sup>T</sup>**X**. *λ*<sub>(*k*)</sub> is equal to the sum of the squares over the dataset associated with each component *k*, that is, *λ*<sub>(*k*)</sub> = Σ<sub>*i*</sub> *t*<sub>*k*</sub><sup>2</sup><sub>(*i*)</sub> = Σ<sub>*i*</sub> (**x**<sub>(*i*)</sub> ⋅ **w**<sub>(*k*)</sub>)<sup>2</sup>.

### Dimensionality reduction

The transformation **P** = **X** **W** maps a data vector **x**<sub>(*i*)</sub> from an original space of *x* variables to a new space of *p* variables which are uncorrelated over the dataset. To non-dimensionalize the centered data, let *X<sub>c</sub>* represent the characteristic values of data vectors *X<sub>i</sub>*, given by:

- $\|X\|_{\infty }$ (maximum norm),
- ${\frac {1}{n}}\|X\|_{1}$ (mean absolute value), or
- ${\frac {1}{\sqrt {n}}}\|X\|_{2}$ (normalized Euclidean norm),

for a dataset of size *n*. These norms are used to transform the original space of variables *x, y* to a new space of uncorrelated variables *p, q* (given *Y<sub>c</sub>* with same meaning), such that $p_{i}={\frac {X_{i}}{X_{c}}},\quad q_{i}={\frac {Y_{i}}{Y_{c}}}$; and the new variables are linearly related as: $q=\alpha p$. To find the optimal linear relationship, we minimize the total squared reconstruction error: $E(\alpha )={\frac {1}{1-\alpha ^{2}}}\sum _{i=1}^{n}(\alpha p_{i}-q_{i})^{2}$; such that setting the derivative of the error function to zero $(E'(\alpha )=0)$ yields:$\alpha ={\frac {1}{2}}\left(-\lambda \pm {\sqrt {\lambda ^{2}+4}}\right)$ where$\lambda ={\frac {p\cdot p-q\cdot q}{p\cdot q}}$.

![[media/0fbf276b3d18e30f16ac8722c2565479f5e3f657.png]]
A principal components analysis scatterplot of [Y-STR](https://en.wikipedia.org/wiki/Y-STR) [haplotypes](https://en.wikipedia.org/wiki/Haplotype) calculated from repeat-count values for 37 Y-chromosomal STR markers from 354 individuals.<br />
PCA has successfully found linear combinations of the markers that separate out different clusters corresponding to different lines of individuals' Y-chromosomal genetic descent.

Such [dimensionality reduction](https://en.wikipedia.org/wiki/Dimensionality_reduction) can be a very useful step for visualising and processing high-dimensional datasets, while still retaining as much of the variance in the dataset as possible. For example, selecting *L* = 2 and keeping only the first two principal components finds the two-dimensional plane through the high-dimensional dataset in which the data are most spread out, so if the data contains [clusters](https://en.wikipedia.org/wiki/Cluster_analysis) these too may be most spread out, and therefore most visible to be plotted out in a two-dimensional diagram; whereas if two directions through the data (or two of the original variables) are chosen at random, the clusters may be much less spread apart from each other, and may in fact be much more likely to substantially overlay each other, making them indistinguishable.

Similarly, in [regression analysis](https://en.wikipedia.org/wiki/Regression_analysis), the larger the number of [explanatory variables](https://en.wikipedia.org/wiki/Explanatory_variable) allowed, the greater is the chance of [overfitting](https://en.wikipedia.org/wiki/Overfitting) the model, producing conclusions that fail to generalise to other datasets. One approach, especially when there are strong correlations between different possible explanatory variables, is to reduce them to a few principal components and then run the regression against them, a method called [principal component regression](https://en.wikipedia.org/wiki/Principal_component_regression).

Dimensionality reduction may also be appropriate when the variables in a dataset are noisy. If each column of the dataset contains independent identically distributed Gaussian noise, then the columns of **T** will also contain similarly identically distributed Gaussian noise (such a distribution is invariant under the effects of the matrix **W**, which can be thought of as a high-dimensional rotation of the co-ordinate axes). However, with more of the total variance concentrated in the first few principal components compared to the same noise variance, the proportionate effect of the noise is less—the first few components achieve a higher [signal-to-noise ratio](https://en.wikipedia.org/wiki/Signal-to-noise_ratio). PCA thus can have the effect of concentrating much of the signal into the first few principal components, which can usefully be captured by dimensionality reduction; while the later principal components may be dominated by noise, and so disposed of without great loss. If the dataset is not too large, the significance of the principal components can be tested using [parametric bootstrap](https://en.wikipedia.org/wiki/Bootstrapping_(statistics)#Parametric_bootstrap "Bootstrapping (statistics)"), as an aid in determining how many principal components to retain.

### Singular value decomposition

The principal components transformation can also be associated with another matrix factorization, the [[Singular Value Decomposition]] (SVD) of **X**,

$\mathbf {X} =\mathbf {U} \mathbf {\Sigma } \mathbf {W} ^{T}$

Here **Σ** is an *n*-by-*p* [rectangular diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) of positive numbers *σ*<sub>(*k*)</sub>, called the singular values of **X**; **U** is an *n*-by-*n* matrix, the columns of which are orthogonal unit vectors of length *n* called the left singular vectors of **X**; and **W** is a *p*-by-*p* matrix whose columns are orthogonal unit vectors of length *p* and called the right singular vectors of **X**.

In terms of this factorization, the matrix **X**<sup>T</sup>**X** can be written

${\begin{aligned}\mathbf {X} ^{T}\mathbf {X} &=\mathbf {W} \mathbf {\Sigma } ^{\mathsf {T}}\mathbf {U} ^{\mathsf {T}}\mathbf {U} \mathbf {\Sigma } \mathbf {W} ^{\mathsf {T}}\\&=\mathbf {W} \mathbf {\Sigma } ^{\mathsf {T}}\mathbf {\Sigma } \mathbf {W} ^{\mathsf {T}}\\&=\mathbf {W} \mathbf {\hat {\Sigma }} ^{2}\mathbf {W} ^{\mathsf {T}}\end{aligned}}$

where **$\mathbf {\hat {\Sigma }}$** is the square diagonal matrix with the singular values of **X** and the excess zeros chopped off that satisfies **$\mathbf {{\hat {\Sigma }}^{2}} =\mathbf {\Sigma } ^{\mathsf {T}}\mathbf {\Sigma }$**. Comparison with the eigenvector factorization of **X**<sup>T</sup>**X** establishes that the right singular vectors **W** of **X** are equivalent to the eigenvectors of **X**<sup>T</sup>**X**, while the singular values *σ*<sub>(*k*)</sub> of **$\mathbf {X}$** are equal to the square-root of the eigenvalues *λ*<sub>(*k*)</sub> of **X**<sup>T</sup>**X**.

Using the singular value decomposition the score matrix **T** can be written

${\begin{aligned}\mathbf {T} &=\mathbf {X} \mathbf {W} \\&=\mathbf {U} \mathbf {\Sigma } \mathbf {W} ^{\mathsf {T}}\mathbf {W} \\&=\mathbf {U} \mathbf {\Sigma } \end{aligned}}$

so each column of **T** is given by one of the left singular vectors of **X** multiplied by the corresponding singular value. This form is also the [polar decomposition](https://en.wikipedia.org/wiki/Polar_decomposition) of **T**.

Efficient algorithms exist to calculate the SVD of **X** without having to form the matrix **X**<sup>T</sup>**X**, so computing the SVD is now the standard way to calculate a principal components analysis from a data matrix, unless only a handful of components are required.

As with the eigen-decomposition, a truncated *n* × *L* score matrix **T**<sub>L</sub> can be obtained by considering only the first L largest singular values and their singular vectors:

$\mathbf {T} _{L}=\mathbf {U} _{L}\mathbf {\Sigma } _{L}=\mathbf {X} \mathbf {W} _{L}$

The truncation of a matrix **M** or **T** using a truncated singular value decomposition in this way produces a truncated matrix that is the nearest possible matrix of [rank](https://en.wikipedia.org/wiki/Rank_(linear_algebra) "Rank (linear algebra)") *L* to the original matrix, in the sense of the difference between the two having the smallest possible [Frobenius norm](https://en.wikipedia.org/wiki/Frobenius_norm), a result known as the [Eckart–Young theorem](https://en.wikipedia.org/wiki/Low-rank_approximation#Proof_of_Eckart–Young–Mirsky_theorem_(for_Frobenius_norm) "Low-rank approximation") \[1936\].

> **Theorem (Optimal k‑dimensional fit).** Let P be an n×m data matrix whose columns have been mean‑centered and scaled, and let $P=U\,\Sigma \,V^{T}$ be its singular value decomposition. Then the best rank‑k approximation to P in the least‑squares (Frobenius‑norm) sense is $P_{k}=U_{k}\,\Sigma _{k}\,V_{k}^{T}$, where V<sub>k</sub> consists of the first k columns of V. Moreover, the relative residual variance is $R(k)={\frac {\sum _{j=k+1}^{m}\sigma _{j}^{2}}{\sum _{j=1}^{m}\sigma _{j}^{2}}}$.



## Further considerations

The singular values (in **Σ**) are the square roots of the [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of the matrix **X**<sup>T</sup>**X**. Each eigenvalue is proportional to the portion of the "variance" (more correctly of the sum of the squared distances of the points from their multidimensional mean) that is associated with each eigenvector. The sum of all the eigenvalues is equal to the sum of the squared distances of the points from their multidimensional mean. PCA essentially rotates the set of points around their mean in order to align with the principal components. This moves as much of the variance as possible (using an orthogonal transformation) into the first few dimensions. The values in the remaining dimensions, therefore, tend to be small and may be dropped with minimal loss of information (see [below](https://en.wikipedia.org/wiki/Principle_Component_Analysis#PCA_and_information_theory)). PCA is often used in this manner for [dimensionality reduction](https://en.wikipedia.org/wiki/Dimensionality_reduction). PCA has the distinction of being the optimal orthogonal transformation for keeping the subspace that has largest "variance" (as defined above). This advantage, however, comes at the price of greater computational requirements if compared, for example, and when applicable, to the [discrete cosine transform](https://en.wikipedia.org/wiki/Discrete_cosine_transform), and in particular to the DCT-II which is simply known as the "DCT". [Nonlinear dimensionality reduction](https://en.wikipedia.org/wiki/Nonlinear_dimensionality_reduction) techniques tend to be more computationally demanding than PCA.

PCA is sensitive to the scaling of the variables. Mathematically this sensitivity comes from the way a rescaling changes the sample‑covariance matrix that PCA diagonalises.

Let $\mathbf {X} _{\text{c}}$ be the \*centered\* data matrix (*n* rows, *p* columns) and define the covariance $\Sigma ={\frac {1}{n}}\,\mathbf {X} _{\text{c}}^{\mathsf {T}}\mathbf {X} _{\text{c}}.$ If the $j$‑th variable is multiplied by a factor $\alpha _{j}$ we obtain $\mathbf {X} _{\text{c}}^{(\alpha )}=\mathbf {X} _{\text{c}}D,\qquad D=\operatorname {diag} (\alpha _{1},\ldots ,\alpha _{p}).$ Hence the new covariance is $\Sigma ^{(\alpha )}=D^{\mathsf {T}}\,\Sigma \,D.$

Because the eigenvalues and eigenvectors of $\Sigma ^{(\alpha )}$ are those of $\Sigma$ scaled by $D$, the principal axes rotate toward any column whose variance has been inflated, exactly as the 2‑D example below illustrates.

If we have just two variables and they have the same [sample variance](https://en.wikipedia.org/wiki/Sample_variance) and are completely correlated, then the PCA will entail a rotation by 45° and the "weights" (they are the cosines of rotation) for the two variables with respect to the principal component will be equal. But if we multiply all values of the first variable by 100, then the first principal component will be almost the same as that variable, with a small contribution from the other variable, whereas the second component will be almost aligned with the second original variable. This means that whenever the different variables have different units (like temperature and mass), PCA is a somewhat arbitrary method of analysis. (Different results would be obtained if one used Fahrenheit rather than Celsius for example.) Pearson's original paper was entitled "On Lines and Planes of Closest Fit to Systems of Points in Space" – "in space" implies physical Euclidean space where such concerns do not arise. One way of making the PCA less arbitrary is to use variables scaled so as to have unit variance, by standardizing the data and hence use the autocorrelation matrix instead of the autocovariance matrix as a basis for PCA. However, this compresses (or expands) the fluctuations in all dimensions of the signal space to unit variance.

Classical PCA assumes the cloud of points has already been translated so its centroid is at the origin.

Write each observation as $\mathbf {q} _{i}={\boldsymbol {\mu }}+\mathbf {z} _{i},\qquad {\boldsymbol {\mu }}={\tfrac {1}{n}}\sum _{i=1}^{n}\mathbf {q} _{i}.$

Without subtracting ${\boldsymbol {\mu }}$ we are in effect diagonalising

$\Sigma _{\text{unc}}\;=\;n\,{\boldsymbol {\mu }}{\boldsymbol {\mu }}^{\mathsf {T}}\;+\;{\tfrac {1}{n}}\,\mathbf {Z} ^{\mathsf {T}}\mathbf {Z} ,$

where $\mathbf {Z}$ is the centered matrix. The rank‑one term $n\,{\boldsymbol {\mu }}{\boldsymbol {\mu }}^{\mathsf {T}}$ often dominates, forcing the leading eigenvector to point almost exactly toward the mean and obliterating any structure in the centred part $\mathbf {Z}$. After mean subtraction that term vanishes and the principal axes align with the true directions of maximal variance.

Mean-centering is unnecessary if performing a principal components analysis on a correlation matrix, as the data are already centered after calculating correlations. Correlations are derived from the cross-product of two standard scores (Z-scores) or statistical moments (hence the name: *Pearson Product-Moment Correlation*). Also see the article by Kromrey & Foster-Johnson (1998) on *"Mean-centering in Moderated Regression: Much Ado About Nothing"*. Since [covariances are correlations of normalized variables](https://en.wikipedia.org/wiki/Covariance_matrix#Relation_to_the_correlation_matrix) ([Z- or standard-scores](https://en.wikipedia.org/wiki/Standard_score#Calculation)) a PCA based on the correlation matrix of **X** is [equal](https://en.wikipedia.org/wiki/Equality_(mathematics) "Equality (mathematics)") to a PCA based on the covariance matrix of **Z**, the standardized version of **X**.

PCA is a popular primary technique in [pattern recognition](https://en.wikipedia.org/wiki/Pattern_recognition). It is not, however, optimized for class separability. However, it has been used to quantify the distance between two or more classes by calculating center of mass for each class in principal component space and reporting Euclidean distance between center of mass of two or more classes. The [linear discriminant analysis](https://en.wikipedia.org/wiki/Linear_discriminant_analysis) is an alternative which is optimized for class separability.

## Table of symbols and abbreviations

<table class="wikitable">

Symbol
Meaning
Dimensions
Indices

&#10;
$\mathbf {X} =[X_{ij}]$
data matrix, consisting of the set of all data vectors, one vector per row
$n\times p$
$i=1\ldots n$<br />
$j=1\ldots p$

$n$
the number of row vectors in the data set
$1\times 1$
<em>scalar</em>

$p$
the number of elements in each row vector (dimension)
$1\times 1$
<em>scalar</em>

$L$
the number of dimensions in the dimensionally reduced subspace, $1\leq L\leq p$
$1\times 1$
<em>scalar</em>

$\mathbf {u} =[u_{j}]$
vector of empirical [means](https://en.wikipedia.org/wiki/Mean), one mean for each column <em>j</em> of the data matrix
$p\times 1$
$j=1\ldots p$

$\mathbf {s} =[s_{j}]$
vector of empirical [standard deviations](https://en.wikipedia.org/wiki/Standard_deviation), one standard deviation for each column <em>j</em> of the data matrix
$p\times 1$
$j=1\ldots p$

$\mathbf {h} =[h_{i}]$
vector of all 1's
$1\times n$
$i=1\ldots n$

$\mathbf {B} =[B_{ij}]$
[deviations](https://en.wikipedia.org/wiki/Standard_deviation) from the mean of each column <em>j</em> of the data matrix
$n\times p$
$i=1\ldots n$<br />
$j=1\ldots p$

$\mathbf {Z} =[Z_{ij}]$
[z-scores](https://en.wikipedia.org/wiki/Z-score), computed using the mean and standard deviation for each column <em>j</em> of the data matrix
$n\times p$
$i=1\ldots n$<br />
$j=1\ldots p$

$\mathbf {C} =[C_{jj'}]$
[covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix)
$p\times p$
$j=1\ldots p$<br />
$j'=1\ldots p$

$\mathbf {R} =[R_{jj'}]$
[correlation matrix](https://en.wikipedia.org/wiki/Correlation_matrix)
$p\times p$
$j=1\ldots p$<br />
$j'=1\ldots p$

$\mathbf {V} =[V_{jj'}]$
matrix consisting of the set of all [eigenvectors](https://en.wikipedia.org/wiki/Eigenvectors) of <strong>C</strong>, one eigenvector per column
$p\times p$
$j=1\ldots p$<br />
$j'=1\ldots p$

$\mathbf {D} =[D_{jj'}]$
[diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) consisting of the set of all [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalues) of <strong>C</strong> along its [principal diagonal](https://en.wikipedia.org/wiki/Principal_diagonal), and 0 for all other elements ( note $\mathbf {\Lambda }$ used above )
$p\times p$
$j=1\ldots p$<br />
$j'=1\ldots p$

$\mathbf {W} =[W_{jl}]$
matrix of basis vectors, one vector per column, where each basis vector is one of the eigenvectors of <strong>C</strong>, and where the vectors in <strong>W</strong> are a sub-set of those in <strong>V</strong>
$p\times L$
$j=1\ldots p$<br />
$l=1\ldots L$

$\mathbf {T} =[T_{il}]$
matrix consisting of <em>n</em> row vectors, where each vector is the projection of the corresponding data vector from matrix <strong>X</strong> onto the basis vectors contained in the columns of matrix <strong>W</strong>.
$n\times L$
$i=1\ldots n$<br />
$l=1\ldots L$

</table>

## Properties and limitations

### Properties

Some properties of PCA include:

***Property 1*:** For any integer *q*, 1 ≤ *q* ≤ *p*, consider the orthogonal [[Linear Transformation]]

$y=\mathbf {B'} x$

where $y$ is a *q-element* vector and $\mathbf {B'}$ is a (*q* × *p*) matrix, and let $\mathbf {\Sigma } _{y}=\mathbf {B'} \mathbf {\Sigma } \mathbf {B}$ be the [variance](https://en.wikipedia.org/wiki/Variance)-[covariance](https://en.wikipedia.org/wiki/Covariance) matrix for $y$. Then the trace of $\mathbf {\Sigma } _{y}$, denoted $\operatorname {tr} (\mathbf {\Sigma } _{y})$, is maximized by taking $\mathbf {B} =\mathbf {A} _{q}$, where $\mathbf {A} _{q}$ consists of the first *q* columns of $\mathbf {A}$ $(\mathbf {B'}$ is the transpose of $\mathbf {B} )$. ($\mathbf {A}$ is not defined here)

***Property 2*:** Consider again the [orthonormal transformation](https://en.wikipedia.org/wiki/Orthonormal_transformation)

$y=\mathbf {B'} x$

with $x,\mathbf {B} ,\mathbf {A}$ and $\mathbf {\Sigma } _{y}$ defined as before. Then $\operatorname {tr} (\mathbf {\Sigma } _{y})$ is minimized by taking $\mathbf {B} =\mathbf {A} _{q}^{*},$ where $\mathbf {A} _{q}^{*}$ consists of the last *q* columns of $\mathbf {A}$.

The statistical implication of this property is that the last few PCs are not simply unstructured left-overs after removing the important PCs. Because these last PCs have variances as small as possible they are useful in their own right. They can help to detect unsuspected near-constant linear relationships between the elements of x, and they may also be useful in [regression](https://en.wikipedia.org/wiki/Regression_analysis), in selecting a subset of variables from x, and in outlier detection.

***Property 3*:** (Spectral decomposition of **Σ**)

$\mathbf {\Sigma } =\lambda _{1}\alpha _{1}\alpha _{1}'+\cdots +\lambda _{p}\alpha _{p}\alpha _{p}'$

Before we look at its usage, we first look at [diagonal](https://en.wikipedia.org/wiki/Diagonal) elements,

$\operatorname {Var} (x_{j})=\sum _{k=1}^{P}\lambda _{k}\alpha _{kj}^{2}$

Then, perhaps the main statistical implication of the result is that not only can we decompose the combined variances of all the elements of x into decreasing contributions due to each PC, but we can also decompose the whole [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) into contributions $\lambda _{k}\alpha _{k}\alpha _{k}'$ from each PC. Although not strictly decreasing, the elements of $\lambda _{k}\alpha _{k}\alpha _{k}'$ will tend to become smaller as $k$ increases, as $\lambda _{k}\alpha _{k}\alpha _{k}'$ is nonincreasing for increasing $k$, whereas the elements of $\alpha _{k}$ tend to stay about the same size because of the normalization constraints: $\alpha _{k}'\alpha _{k}=1,k=1,\dots ,p$.

### Limitations

As noted above, the results of PCA depend on the scaling of the variables. This can be cured by scaling each feature by its standard deviation, so that one ends up with dimensionless features with unital variance.

The applicability of PCA as described above is limited by certain (tacit) assumptions made in its derivation. In particular, PCA can capture linear correlations between the features but fails when this assumption is violated (see Figure 6a in the reference). In some cases, coordinate transformations can restore the linearity assumption and PCA can then be applied (see [kernel PCA](https://en.wikipedia.org/wiki/Kernel_principal_component_analysis)).

Another limitation is the mean-removal process before constructing the covariance matrix for PCA. In fields such as astronomy, all the signals are non-negative, and the mean-removal process will force the mean of some astrophysical exposures to be zero, which consequently creates unphysical negative fluxes, and forward modeling has to be performed to recover the true magnitude of the signals. As an alternative method, [non-negative matrix factorization](https://en.wikipedia.org/wiki/Non-negative_matrix_factorization) focusing only on the non-negative elements in the matrices is well-suited for astrophysical observations. See more at [the relation between PCA and non-negative matrix factorization](#Non-negative_matrix_factorization).

PCA is at a disadvantage if the data has not been standardized before applying the algorithm to it. PCA transforms the original data into data that is relevant to the principal components of that data, which means that the new data variables cannot be interpreted in the same ways that the originals were. They are linear interpretations of the original variables. Also, if PCA is not performed properly, there is a high likelihood of information loss.

PCA relies on a linear model. If a dataset has a pattern hidden inside it that is nonlinear, then PCA can actually steer the analysis in the complete opposite direction of progress. Researchers at Kansas State University discovered that the sampling error in their experiments impacted the bias of PCA results. "If the number of subjects or blocks is smaller than 30, and/or the researcher is interested in PC's beyond the first, it may be better to first correct for the serial correlation, before PCA is conducted". The researchers at Kansas State also found that PCA could be "seriously biased if the autocorrelation structure of the data are not correctly handled".

### PCA and information theory

Dimensionality reduction results in a loss of information, in general. PCA-based dimensionality reduction tends to minimize that information loss, under certain signal and noise models.

Under the assumption that

$\mathbf {x} =\mathbf {s} +\mathbf {n} ,$

that is, that the data vector $\mathbf {x}$ is the sum of the desired information-bearing signal $\mathbf {s}$ and a noise signal $\mathbf {n}$ one can show that PCA can be optimal for dimensionality reduction, from an information-theoretic point-of-view.

In particular, Linsker showed that if $\mathbf {s}$ is Gaussian and $\mathbf {n}$ is Gaussian noise with a covariance matrix proportional to the identity matrix, the PCA maximizes the [[Mutual Information]] $I(\mathbf {y} ;\mathbf {s} )$ between the desired information $\mathbf {s}$ and the dimensionality-reduced output $\mathbf {y} =\mathbf {W} _{L}^{T}\mathbf {x}$.

If the noise is still Gaussian and has a covariance matrix proportional to the identity matrix (that is, the components of the vector $\mathbf {n}$ are [iid](https://en.wikipedia.org/wiki/Iid)), but the information-bearing signal $\mathbf {s}$ is non-Gaussian (which is a common scenario), PCA at least minimizes an upper bound on the *information loss*, which is defined as

$I(\mathbf {x} ;\mathbf {s} )-I(\mathbf {y} ;\mathbf {s} ).$

The optimality of PCA is also preserved if the noise $\mathbf {n}$ is iid and at least more Gaussian (in terms of the [[Kullback-Leibler Divergence|Kullback–Leibler divergence]]) than the information-bearing signal $\mathbf {s}$. In general, even if the above signal model holds, PCA loses its information-theoretic optimality as soon as the noise $\mathbf {n}$ becomes dependent.

## Computation using the covariance method

The following is a detailed description of PCA using the covariance method as opposed to the correlation method.

The goal is to transform a given data set **X** of dimension *p* to an alternative data set **Y** of smaller dimension *L*. Equivalently, we are seeking to find the matrix **Y**, where **Y** is the [Karhunen–Loève](https://en.wikipedia.org/wiki/Karhunen%E2%80%93Lo%C3%A8ve_theorem) transform (KLT) of matrix **X**:

$$
\mathbf {Y} =\mathbb {KLT} \{\mathbf {X} \}
$$

1.  **Organize the data set**

    Suppose you have data comprising a set of observations of *p* variables, and you want to reduce the data so that each observation can be described with only *L* variables, *L* \< *p*. Suppose further, that the data are arranged as a set of *n* data vectors $\mathbf {x} _{1}\ldots \mathbf {x} _{n}$ with each $\mathbf {x} _{i}$ representing a single grouped observation of the *p* variables.

    - Write $\mathbf {x} _{1}\ldots \mathbf {x} _{n}$ as row vectors, each with *p* elements.
    - Place the row vectors into a single matrix **X** of dimensions *n* × *p*.

2.  **Calculate the empirical mean**
    - Find the empirical mean along each column *j* = 1, ..., *p*.
    - Place the calculated mean values into an empirical mean vector **u** of dimensions *p* × 1. 

$$
u_{j}={\frac {1}{n}}\sum _{i=1}^{n}X_{ij}
$$

3.  **Calculate the deviations from the mean**

    Mean subtraction is an integral part of the solution towards finding a principal component basis that minimizes the mean square error of approximating the data. Hence we proceed by centering the data as follows:

    - Subtract the empirical mean vector $\mathbf {u} ^{T}$ from each row of the data matrix **X**.
    - Store mean-subtracted data in the *n* × *p* matrix **B**. 

$$
\mathbf {B} =\mathbf {X} -\mathbf {h} \mathbf {u} ^{T}
$$

 where **h** is an *n* × 1 column vector of all 1s: 

$$
h_{i}=1\,\qquad \qquad {\text{for }}i=1,\ldots ,n
$$

    In some applications, each variable (column of **B**) may also be scaled to have a variance equal to 1 (see [Z-score](https://en.wikipedia.org/wiki/Z-score)). This step affects the calculated principal components, but makes them independent of the units used to measure the different variables.

4.  **Find the covariance matrix**
    - Find the *p* × *p* empirical [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) **C** from matrix **B**: 

$$
\mathbf {C} ={1 \over {n-1}}\mathbf {B} ^{*}\mathbf {B}
$$

 where $*$ is the [conjugate transpose](https://en.wikipedia.org/wiki/Conjugate_transpose) operator. If **B** consists entirely of real numbers, which is the case in many applications, the "conjugate transpose" is the same as the regular [transpose](https://en.wikipedia.org/wiki/Transpose).
    - The reasoning behind using *n* − 1 instead of *n* to calculate the covariance is [Bessel's correction](https://en.wikipedia.org/wiki/Bessel%27s_correction).

5.  **Find the eigenvectors and eigenvalues of the covariance matrix**
    - Compute the matrix **V** of [eigenvectors](https://en.wikipedia.org/wiki/Eigenvector) which [diagonalizes](https://en.wikipedia.org/wiki/Diagonalizable_matrix) the covariance matrix **C**: 

$$
\mathbf {V} ^{-1}\mathbf {C} \mathbf {V} =\mathbf {D}
$$

 where **D** is the [diagonal matrix](https://en.wikipedia.org/wiki/Diagonal_matrix) of [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalue) of **C**. This step will typically involve the use of a computer-based algorithm for [computing eigenvectors and eigenvalues](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix). These algorithms are readily available as sub-components of most [matrix algebra](https://en.wikipedia.org/wiki/Matrix_algebra) systems, such as [SAS](https://en.wikipedia.org/wiki/SAS_(software) "SAS (software)"), [R](https://en.wikipedia.org/wiki/R_(programming_language) "R (programming language)"), [MATLAB](https://en.wikipedia.org/wiki/MATLAB), [Mathematica](https://en.wikipedia.org/wiki/Mathematica), [SciPy](https://en.wikipedia.org/wiki/SciPy), [IDL](https://en.wikipedia.org/wiki/IDL_(programming_language) "IDL (programming language)") ([Interactive Data Language](https://en.wikipedia.org/wiki/Interactive_Data_Language)), or [GNU Octave](https://en.wikipedia.org/wiki/GNU_Octave) as well as [OpenCV](https://en.wikipedia.org/wiki/OpenCV).
    - Matrix **D** will take the form of an *p* × *p* diagonal matrix, where 

$$
D_{k\ell }=\lambda _{k}\qquad {\text{for }}k=\ell
$$

 is the *j*th eigenvalue of the covariance matrix **C**, and 

$$
D_{k\ell }=0\qquad {\text{for }}k\neq \ell .
$$

    - Matrix **V**, also of dimension *p* × *p*, contains *p* column vectors, each of length *p*, which represent the *p* eigenvectors of the covariance matrix **C**.
    - The eigenvalues and eigenvectors are ordered and paired. The *j*th eigenvalue corresponds to the *j*th eigenvector.
    - Matrix **V** denotes the matrix of *right* eigenvectors (as opposed to *left* eigenvectors). In general, the matrix of right eigenvectors need *not* be the (conjugate) transpose of the matrix of left eigenvectors.

6.  **Rearrange the eigenvectors and eigenvalues**
    - Sort the columns of the eigenvector matrix **V** and eigenvalue matrix **D** in order of *decreasing* eigenvalue.
    - Make sure to maintain the correct pairings between the columns in each matrix.

7.  **Compute the cumulative energy content for each eigenvector**
    - The eigenvalues represent the distribution of the source data's energy<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup> among each of the eigenvectors, where the eigenvectors form a [basis](https://en.wikipedia.org/wiki/Basis_(linear_algebra) "Basis (linear algebra)") for the data. The cumulative energy content *g* for the *j*th eigenvector is the sum of the energy content across all of the eigenvalues from 1 through *j* divided by the sum of energy content across all eigenvalues (shown in step 8):<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> 

$$
g_{j}=\sum _{k=1}^{j}D_{kk}\qquad {\text{for }}j=1,\dots ,p
$$

8.  **Select a subset of the eigenvectors as basis vectors**
    - Save the first *L* columns of **V** as the *p* × *L* matrix **W**: 

$$
W_{kl}=V_{k\ell }\qquad {\text{for }}k=1,\dots ,p\qquad \ell =1,\dots ,L
$$

 where 

$$
1\leq L\leq p.
$$

    - Use the vector **g** as a guide in choosing an appropriate value for *L*. The goal is to choose a value of *L* as small as possible while achieving a reasonably high value of *g* on a percentage basis. For example, you may want to choose *L* so that the cumulative energy *g* is above a certain threshold, like 90 percent. In this case, choose the smallest value of *L* such that 

$$
{\frac {g_{L}}{g_{p}}}\geq 0.9
$$

9.  **Project the data onto the new basis**
    - The projected data points are the rows of the matrix 

$$
\mathbf {T} =\mathbf {B} \cdot \mathbf {W}
$$

    That is, the first column of $\mathbf {T}$ is the projection of the data points onto the first principal component, the second column is the projection onto the second principal component, etc.

## Derivation using the covariance method

Let **X** be a *d*-dimensional random vector expressed as column vector. Without loss of generality, assume **X** has zero mean.

We want to find $(\ast )$ a *d* × *d* [orthonormal transformation matrix](https://en.wikipedia.org/wiki/Orthonormal_basis) **P** so that **PX** has a diagonal covariance matrix (that is, **PX** is a random vector with all its distinct components pairwise uncorrelated).

A quick computation assuming $P$ were unitary yields:

${\begin{aligned}\operatorname {cov} (PX)&=\operatorname {E} [PX~(PX)^{*}]\\&=\operatorname {E} [PX~X^{*}P^{*}]\\&=P\operatorname {E} [XX^{*}]P^{*}\\&=P\operatorname {cov} (X)P^{-1}\\\end{aligned}}$

Hence $(\ast )$ holds if and only if $\operatorname {cov} (X)$ were diagonalisable by $P$.

This is very constructive, as cov(**X**) is guaranteed to be a non-negative definite matrix and thus is guaranteed to be diagonalisable by some unitary matrix.

## Covariance-free computation

In practical implementations, especially with [high dimensional data](https://en.wikipedia.org/wiki/High_dimensional_data) (large p), the naive covariance method is rarely used because it is not efficient due to high computational and memory costs of explicitly determining the covariance matrix. The covariance-free approach avoids the *np*<sup>2</sup> operations of explicitly calculating and storing the covariance matrix **X<sup>T</sup>X**, instead utilizing one of [matrix-free methods](https://en.wikipedia.org/wiki/Matrix-free_methods), for example, based on the function evaluating the product **X<sup>T</sup>(X r)** at the cost of 2*np* operations.

### Iterative computation

One way to compute the first principal component efficiently is shown in the following pseudo-code, for a data matrix **X** with zero mean, without ever computing its covariance matrix.

    r = a random vector of length p
    r = r / norm(r)
    do c times:
          s = 0 (a vector of length p)
          for each row x in X
                s = s + (x ⋅ r) x
          λ = rTs // λ is the eigenvalue
          error = |λ ⋅ r − s|
          r = s / norm(s)
          exit if error < tolerance
    return λ, r

This [[Power Iteration]] algorithm simply calculates the vector **X<sup>T</sup>(X r)**, normalizes, and places the result back in **r**. The eigenvalue is approximated by **r<sup>T</sup> (X<sup>T</sup>X) r**, which is the [Rayleigh quotient](https://en.wikipedia.org/wiki/Rayleigh_quotient) on the unit vector **r** for the covariance matrix **X<sup>T</sup>X** . If the largest singular value is well separated from the next largest one, the vector **r** gets close to the first principal component of **X** within the number of iterations c, which is small relative to p, at the total cost *2cnp*. The [[Power Iteration]] convergence can be accelerated without noticeably sacrificing the small cost per iteration using more advanced [matrix-free methods](https://en.wikipedia.org/wiki/Matrix-free_methods), such as the [Lanczos algorithm](https://en.wikipedia.org/wiki/Lanczos_algorithm) or the Locally Optimal Block Preconditioned Conjugate Gradient ([LOBPCG](https://en.wikipedia.org/wiki/LOBPCG)) method.

Subsequent principal components can be computed one-by-one via deflation or simultaneously as a block. In the former approach, imprecisions in already computed approximate principal components additively affect the accuracy of the subsequently computed principal components, thus increasing the error with every new computation. The latter approach in the block power method replaces single-vectors **r** and **s** with block-vectors, matrices **R** and **S**. Every column of **R** approximates one of the leading principal components, while all columns are iterated simultaneously. The main calculation is evaluation of the product **X<sup>T</sup>(X R)**. Implemented, for example, in [LOBPCG](https://en.wikipedia.org/wiki/LOBPCG), efficient blocking eliminates the accumulation of the errors, allows using high-level [BLAS](https://en.wikipedia.org/wiki/BLAS) matrix-matrix product functions, and typically leads to faster convergence, compared to the single-vector one-by-one technique.

### The NIPALS method

*Non-linear iterative partial least squares (NIPALS)* is a variant the classical [[Power Iteration]] with matrix deflation by subtraction implemented for computing the first few components in a principal component or [partial least squares](https://en.wikipedia.org/wiki/Partial_least_squares) analysis. For very-high-dimensional datasets, such as those generated in the \*omics sciences (for example, [genomics](https://en.wikipedia.org/wiki/Genomics), [metabolomics](https://en.wikipedia.org/wiki/Metabolomics)) it is usually only necessary to compute the first few PCs. The [non-linear iterative partial least squares](https://en.wikipedia.org/wiki/Non-linear_iterative_partial_least_squares) (NIPALS) algorithm updates iterative approximations to the leading scores and loadings **t**<sub>1</sub> and **r**<sub>1</sub><sup>T</sup> by the [[Power Iteration]] multiplying on every iteration by **X** on the left and on the right, that is, calculation of the covariance matrix is avoided, just as in the matrix-free implementation of the power iterations to **X<sup>T</sup>X**, based on the function evaluating the product **X<sup>T</sup>(X r)** = **((X r)<sup>T</sup>X)<sup>T</sup>**.

The matrix deflation by subtraction is performed by subtracting the outer product, **t**<sub>1</sub>**r**<sub>1</sub><sup>T</sup> from **X** leaving the deflated residual matrix used to calculate the subsequent leading PCs. For large data matrices, or matrices that have a high degree of column collinearity, NIPALS suffers from loss of orthogonality of PCs due to machine precision [round-off errors](https://en.wikipedia.org/wiki/Round-off_errors) accumulated in each iteration and matrix deflation by subtraction. A [Gram–Schmidt](https://en.wikipedia.org/wiki/Gram%E2%80%93Schmidt) re-orthogonalization algorithm is applied to both the scores and the loadings at each iteration step to eliminate this loss of orthogonality. NIPALS reliance on single-vector multiplications cannot take advantage of high-level [BLAS](https://en.wikipedia.org/wiki/BLAS) and results in slow convergence for clustered leading singular values—both these deficiencies are resolved in more sophisticated matrix-free block solvers, such as the Locally Optimal Block Preconditioned Conjugate Gradient ([LOBPCG](https://en.wikipedia.org/wiki/LOBPCG)) method.

### Online/sequential estimation

In an "online" or "streaming" situation with data arriving piece by piece rather than being stored in a single batch, it is useful to make an estimate of the PCA projection that can be updated sequentially. This can be done efficiently, but requires different algorithms.

## Qualitative variables

In PCA, it is common that we want to introduce qualitative variables as supplementary elements. For example, many quantitative variables have been measured on plants. For these plants, some qualitative variables are available as, for example, the species to which the plant belongs. These data were subjected to PCA for quantitative variables. When analyzing the results, it is natural to connect the principal components to the qualitative variable *species*. For this, the following results are produced.

- Identification, on the factorial planes, of the different species, for example, using different colors.
- Representation, on the factorial planes, of the centers of gravity of plants belonging to the same species.
- For each center of gravity and each axis, p-value to judge the significance of the difference between the center of gravity and origin.

These results are what is called *introducing a qualitative variable as supplementary element*. This procedure is detailed in and Husson, Lê, & Pagès (2009) and Pagès (2013). Few software offer this option in an "automatic" way. This is the case of [SPAD](http://www.coheris.com/produits/analytics/logiciel-data-mining/) that historically, following the work of [Ludovic Lebart](https://en.wikipedia.org/wiki/Ludovic_Lebart), was the first to propose this option, and the R package [FactoMineR](http://factominer.free.fr/).

## Applications

### Intelligence

The earliest application of factor analysis was in locating and measuring components of human intelligence. It was believed that intelligence had various uncorrelated components such as spatial intelligence, verbal intelligence, induction, deduction etc and that scores on these could be adduced by factor analysis from results on various tests, to give a single index known as the [Intelligence Quotient](https://en.wikipedia.org/wiki/Intelligence_quotient) (IQ). The pioneering statistical psychologist [Spearman](https://en.wikipedia.org/wiki/Charles_Spearman) actually developed factor analysis in 1904 for his [two-factor theory](https://en.wikipedia.org/wiki/Two-factor_theory_of_intelligence) of intelligence, adding a formal technique to the science of [psychometrics](https://en.wikipedia.org/wiki/Psychometrics). In 1924 [Thurstone](https://en.wikipedia.org/wiki/Louis_Leon_Thurstone) looked for 56 factors of intelligence, developing the notion of Mental Age. Standard IQ tests today are based on this early work.

### Residential differentiation

In 1949, Shevky and Williams introduced the theory of **factorial ecology**, which dominated studies of residential differentiation from the 1950s to the 1970s. Neighbourhoods in a city were recognizable or could be distinguished from one another by various characteristics which could be reduced to three by factor analysis. These were known as 'social rank' (an index of occupational status), 'familism' or family size, and 'ethnicity'; Cluster analysis could then be applied to divide the city into clusters or precincts according to values of the three key factor variables. An extensive literature developed around factorial ecology in urban geography, but the approach went out of fashion after 1980 as being methodologically primitive and having little place in postmodern geographical paradigms.

One of the problems with factor analysis has always been finding convincing names for the various artificial factors. In 2000, Flood revived the factorial ecology approach to show that principal components analysis actually gave meaningful answers directly, without resorting to factor rotation. The principal components were actually dual variables or shadow prices of 'forces' pushing people together or apart in cities. The first component was 'accessibility', the classic trade-off between demand for travel and demand for space, around which classical urban economics is based. The next two components were 'disadvantage', which keeps people of similar status in separate neighbourhoods (mediated by planning), and ethnicity, where people of similar ethnic backgrounds try to co-locate.

About the same time, the Australian Bureau of Statistics defined distinct indexes of advantage and disadvantage taking the first principal component of sets of key variables that were thought to be important. These SEIFA indexes are regularly published for various jurisdictions, and are used frequently in spatial analysis.

### Development indexes

PCA can be used as a formal method for the development of indexes. As an alternative [confirmatory composite analysis](https://en.wikipedia.org/wiki/Confirmatory_composite_analysis) has been proposed to develop and assess indexes.

The City Development Index was developed by PCA from about 200 indicators of city outcomes in a 1996 survey of 254 global cities. The first principal component was subject to iterative regression, adding the original variables singly until about 90% of its variation was accounted for. The index ultimately used about 15 indicators but was a good predictor of many more variables. Its comparative value agreed very well with a subjective assessment of the condition of each city. The coefficients on items of infrastructure were roughly proportional to the average costs of providing the underlying services, suggesting the Index was actually a measure of effective physical and social investment in the city.

The country-level [Human Development Index](https://en.wikipedia.org/wiki/Human_Development_Index) (HDI) from [UNDP](https://en.wikipedia.org/wiki/United_Nations_Development_Programme), which has been published since 1990 and is very extensively used in development studies, has very similar coefficients on similar indicators, strongly suggesting it was originally constructed using PCA.

### Population genetics

In 1978 [Cavalli-Sforza](https://en.wikipedia.org/wiki/Luigi_Luca_Cavalli-Sforza) and others pioneered the use of principal components analysis (PCA) to summarise data on variation in human gene frequencies across regions. The components showed distinctive patterns, including gradients and sinusoidal waves. They interpreted these patterns as resulting from specific ancient migration events.

Since then, PCA has been ubiquitous in population genetics, with thousands of papers using PCA as a display mechanism. Genetics varies largely according to proximity, so the first two principal components actually show spatial distribution and may be used to map the relative geographical location of different population groups, thereby showing individuals who have wandered from their original locations.

PCA in genetics has been technically controversial, in that the technique has been performed on discrete non-normal variables and often on binary allele markers. The lack of any measures of standard error in PCA are also an impediment to more consistent usage. In August 2022, the molecular biologist [Eran Elhaik](https://en.wikipedia.org/wiki/Eran_Elhaik) published a theoretical paper in [Scientific Reports](https://en.wikipedia.org/wiki/Scientific_Reports) analyzing 12 PCA applications. He concluded that it was easy to manipulate the method, which, in his view, generated results that were 'erroneous, contradictory, and absurd.' Specifically, he argued, the results achieved in population genetics were characterized by cherry-picking and [circular reasoning](https://en.wikipedia.org/wiki/Circular_reasoning).

### Market research and indexes of attitude

Market research has been an extensive user of PCA. It is used to develop customer satisfaction or customer loyalty scores for products, and with clustering, to develop market segments that may be targeted with advertising campaigns, in much the same way as factorial ecology will locate geographical areas with similar characteristics.

PCA rapidly transforms large amounts of data into smaller, easier-to-digest variables that can be more rapidly and readily analyzed. In any consumer questionnaire, there are series of questions designed to elicit consumer attitudes, and principal components seek out latent variables underlying these attitudes. For example, the Oxford Internet Survey in 2013 asked 2000 people about their attitudes and beliefs, and from these analysts extracted four principal component dimensions, which they identified as 'escape', 'social networking', 'efficiency', and 'problem creating'.

Another example from Joe Flood in 2008 extracted an attitudinal index toward housing from 28 attitude questions in a national survey of 2697 households in Australia. The first principal component represented a general attitude toward property and home ownership. The index, or the attitude questions it embodied, could be fed into a General Linear Model of tenure choice. The strongest determinant of private renting by far was the attitude index, rather than income, marital status or household type.

### Quantitative finance

In [quantitative finance](https://en.wikipedia.org/wiki/Quantitative_finance), PCA is used in [financial risk management](https://en.wikipedia.org/wiki/Financial_risk_management), and has been applied to [other problems](https://en.wikipedia.org/wiki/Financial_modeling#Quantitative_finance) such as [portfolio optimization](https://en.wikipedia.org/wiki/Portfolio_optimization).

PCA is commonly used in problems involving [fixed income](https://en.wikipedia.org/wiki/Fixed_income) securities and [portfolios](https://en.wikipedia.org/wiki/Bond_fund), and [interest rate derivatives](https://en.wikipedia.org/wiki/Interest_rate_derivative). Valuations here depend on the entire [yield curve](https://en.wikipedia.org/wiki/Yield_curve), comprising numerous highly correlated instruments, and PCA is used to define a set of components or factors that explain rate movements, thereby facilitating the modelling. One common risk management application is to [calculating value at risk](https://en.wikipedia.org/wiki/Value_at_risk#Computation_methods), VaR, applying PCA to the [Monte Carlo simulation](https://en.wikipedia.org/wiki/Monte_Carlo_methods_in_finance).  Here, for each simulation-sample, the components are stressed, and rates, and [in turn option values](https://en.wikipedia.org/wiki/Monte_Carlo_methods_for_option_pricing#Methodology), are then reconstructed; with VaR calculated, finally, over the entire run. PCA is also used in [hedging](https://en.wikipedia.org/wiki/Hedge_(finance) "Hedge (finance)") exposure to [interest rate risk](https://en.wikipedia.org/wiki/Interest_rate_risk), given [partial durations](https://en.wikipedia.org/wiki/Key_rate_duration) and other sensitivities.  Under both, the first three, typically, principal components of the system are of interest ([representing](https://en.wikipedia.org/wiki/Fixed-income_attribution#Modeling_the_yield_curve) "shift", "twist", and "curvature"). These principal components are derived from an eigen-decomposition of the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) of [yield](https://en.wikipedia.org/wiki/Yield_curve) at predefined maturities;  and where the [variance](https://en.wikipedia.org/wiki/Variance) of each component is its [eigenvalue](https://en.wikipedia.org/wiki/Eigenvalue) (and as the components are [orthogonal](https://en.wikipedia.org/wiki/Orthogonal), no correlation need be incorporated in subsequent modelling).

For [equity](https://en.wikipedia.org/wiki/Equity_(finance) "Equity (finance)"), an optimal portfolio is one where the [expected return](https://en.wikipedia.org/wiki/Expected_return) is maximized for a given level of risk, or alternatively, where risk is minimized for a given return; see [Markowitz model](https://en.wikipedia.org/wiki/Markowitz_model) for discussion. Thus, one approach is to reduce portfolio risk, where [allocation strategies](https://en.wikipedia.org/wiki/Asset_allocation) are applied to the "principal portfolios" instead of the underlying [stocks](https://en.wikipedia.org/wiki/Capital_stock). A second approach is to enhance portfolio return, using the principal components to select companies' stocks with upside potential.   PCA has also been used to understand relationships  between international [equity markets](https://en.wikipedia.org/wiki/Equity_market), and within markets between groups of companies in industries or [sectors](https://en.wikipedia.org/wiki/Stock_market_index#Types_of_indices_by_coverage).

PCA may also be applied to [stress testing](https://en.wikipedia.org/wiki/Stress_test_(financial) "Stress test (financial)"), essentially an analysis of a bank's ability to endure [a hypothetical adverse economic scenario](https://en.wikipedia.org/wiki/List_of_bank_stress_tests). Its utility is in "distilling the information contained in \[several\] [macroeconomic variables](https://en.wikipedia.org/wiki/Macroeconomic_model) into a more manageable data set, which can then \[be used\] for analysis." Here, the resulting factors are linked to e.g. interest rates – based on the largest elements of the factor's [eigenvector](https://en.wikipedia.org/wiki/Eigenvector) – and it is then observed how a "shock" to each of the factors affects the implied assets of each of the banks.

### Neuroscience

A variant of principal components analysis is used in [neuroscience](https://en.wikipedia.org/wiki/Neuroscience) to identify the specific properties of a stimulus that increases a [neuron](https://en.wikipedia.org/wiki/Neuron)'s probability of generating an [action potential](https://en.wikipedia.org/wiki/Action_potential). This technique is known as [spike-triggered covariance analysis](https://en.wikipedia.org/wiki/Spike-triggered_covariance). In a typical application an experimenter presents a [white noise](https://en.wikipedia.org/wiki/White_noise) process as a stimulus (usually either as a sensory input to a test subject, or as a [current](https://en.wikipedia.org/wiki/Electric_current) injected directly into the neuron) and records a train of action potentials, or spikes, produced by the neuron as a result. Presumably, certain features of the stimulus make the neuron more likely to spike. In order to extract these features, the experimenter calculates the [covariance matrix](https://en.wikipedia.org/wiki/Covariance_matrix) of the *spike-triggered ensemble*, the set of all stimuli (defined and discretized over a finite time window, typically on the order of 100 ms) that immediately preceded a spike. The [eigenvectors](https://en.wikipedia.org/wiki/Eigenvectors_and_eigenvalues) of the difference between the spike-triggered covariance matrix and the covariance matrix of the *prior stimulus ensemble* (the set of all stimuli, defined over the same length time window) then indicate the directions in the [[Vector Space|space]] of stimuli along which the variance of the spike-triggered ensemble differed the most from that of the prior stimulus ensemble. Specifically, the eigenvectors with the largest positive eigenvalues correspond to the directions along which the variance of the spike-triggered ensemble showed the largest positive change compared to the variance of the prior. Since these were the directions in which varying the stimulus led to a spike, they are often good approximations of the sought after relevant stimulus features.

In neuroscience, PCA is also used to discern the identity of a neuron from the shape of its action potential. [Spike sorting](https://en.wikipedia.org/wiki/Spike_sorting) is an important procedure because [extracellular](https://en.wikipedia.org/wiki/Electrophysiology#Extracellular_recording) recording techniques often pick up signals from more than one neuron. In spike sorting, one first uses PCA to reduce the dimensionality of the space of action potential waveforms, and then performs [clustering analysis](https://en.wikipedia.org/wiki/Cluster_analysis) to associate specific action potentials with individual neurons.

PCA as a dimension reduction technique is particularly suited to detect coordinated activities of large neuronal ensembles. It has been used in determining collective variables, that is, [order parameters](https://en.wikipedia.org/wiki/Order_parameters), during [phase transitions](https://en.wikipedia.org/wiki/Phase_transitions) in the brain.

## Relation with other methods

### Correspondence analysis

[Correspondence analysis](https://en.wikipedia.org/wiki/Correspondence_analysis) (CA) was developed by [Jean-Paul Benzécri](https://en.wikipedia.org/wiki/Jean-Paul_Benz%C3%A9cri) and is conceptually similar to PCA, but scales the data (which should be non-negative) so that rows and columns are treated equivalently. It is traditionally applied to [contingency tables](https://en.wikipedia.org/wiki/Contingency_tables). CA decomposes the [chi-squared statistic](https://en.wikipedia.org/wiki/Chi-squared_statistic) associated to this table into orthogonal factors. Because CA is a descriptive technique, it can be applied to tables for which the chi-squared statistic is appropriate or not. Several variants of CA are available including [detrended correspondence analysis](https://en.wikipedia.org/wiki/Detrended_correspondence_analysis) and [canonical correspondence analysis](https://en.wikipedia.org/wiki/Canonical_correspondence_analysis). One special extension is [multiple correspondence analysis](https://en.wikipedia.org/wiki/Multiple_correspondence_analysis), which may be seen as the counterpart of principal component analysis for categorical data.

### Factor analysis

![[media/5932a5b32f81c864aa17310f6e6acc08c48024d2.jpg]]
The above picture is an example of the difference between PCA and Factor Analysis. In the top diagram the "factor" (e.g., career path) represents the three observed variables (e.g., doctor, lawyer, teacher) whereas in the bottom diagram the observed variables (e.g., pre-school teacher, middle school teacher, high school teacher) are reduced into the component of interest (e.g., teacher).

Principal component analysis creates variables that are linear combinations of the original variables. The new variables have the property that the variables are all orthogonal. The PCA transformation can be helpful as a pre-processing step before clustering. PCA is a variance-focused approach seeking to reproduce the total variable variance, in which components reflect both common and unique variance of the variable. PCA is generally preferred for purposes of data reduction (that is, translating variable space into optimal factor space) but not when the goal is to detect the latent construct or factors.

[Factor analysis](https://en.wikipedia.org/wiki/Factor_analysis) is similar to principal component analysis, in that factor analysis also involves linear combinations of variables. Different from PCA, factor analysis is a correlation-focused approach seeking to reproduce the inter-correlations among variables, in which the factors "represent the common variance of variables, excluding unique variance". In terms of the correlation matrix, this corresponds with focusing on explaining the off-diagonal terms (that is, shared co-variance), while PCA focuses on explaining the terms that sit on the diagonal. However, as a side result, when trying to reproduce the on-diagonal terms, PCA also tends to fit relatively well the off-diagonal correlations. Results given by PCA and factor analysis are very similar in most situations, but this is not always the case, and there are some problems where the results are significantly different. Factor analysis is generally used when the research purpose is detecting data structure (that is, latent constructs or factors) or [causal modeling](https://en.wikipedia.org/wiki/Causal_modeling). If the factor model is incorrectly formulated or the assumptions are not met, then factor analysis will give erroneous results.

### `K`-means clustering

It has been asserted that the relaxed solution of [`k`-means clustering](https://en.wikipedia.org/wiki/K-means_clustering), specified by the cluster indicators, is given by the principal components, and the PCA subspace spanned by the principal directions is identical to the cluster centroid subspace. However, that PCA is a useful relaxation of `k`-means clustering was not a new result, and it is straightforward to uncover counterexamples to the statement that the cluster centroid subspace is spanned by the principal directions.

### Non-negative matrix factorization

![[media/5e5381783423c30e9e34bb3200547215aadaafbf.jpg]]
Fractional residual variance (FRV) plots for PCA and NMF; for PCA, the theoretical values are the contribution from the residual eigenvalues. In comparison, the FRV curves for PCA reaches a flat plateau where no signal are captured effectively; while the NMF FRV curves decline continuously, indicating a better ability to capture signal. The FRV curves for NMF also converges to higher levels than PCA, indicating the less-overfitting property of NMF.

[Non-negative matrix factorization](https://en.wikipedia.org/wiki/Non-negative_matrix_factorization) (NMF) is a dimension reduction method where only non-negative elements in the matrices are used, which is therefore a promising method in astronomy, in the sense that astrophysical signals are non-negative. The PCA components are orthogonal to each other, while the NMF components are all non-negative and therefore constructs a non-orthogonal basis.

In PCA, the contribution of each component is ranked based on the magnitude of its corresponding eigenvalue, which is equivalent to the fractional residual variance (FRV) in analyzing empirical data. For NMF, its components are ranked based only on the empirical FRV curves. The residual fractional eigenvalue plots, that is, $1-\sum _{i=1}^{k}\lambda _{i}{\Big /}\sum _{j=1}^{n}\lambda _{j}$ as a function of component number $k$ given a total of $n$ components, for PCA have a flat plateau, where no data are captured to remove the quasi-static noise, then the curves drop quickly as an indication of over-fitting (random noise). The FRV curves for NMF is decreasing continuously when the NMF components are constructed [sequentially](https://en.wikipedia.org/wiki/Non-negative_matrix_factorization#Sequential_NMF), indicating the continuous capturing of quasi-static noise; then converge to higher levels than PCA, indicating the less over-fitting property of NMF.

### Iconography of correlations

It is often difficult to interpret the principal components when the data include many variables of various origins, or when some variables are qualitative. This leads the PCA user to a delicate elimination of several variables. If observations or variables have an excessive impact on the direction of the axes, they should be removed and then projected as supplementary elements. In addition, it is necessary to avoid interpreting the proximities between the points close to the center of the factorial plane.

![[media/462168117107ccf6c2b483f293d275142b072b0d.jpg]]
Iconography of correlations – Geochemistry of marine aerosols

The [iconography of correlations](https://en.wikipedia.org/wiki/Iconography_of_correlations), on the contrary, which is not a projection on a system of axes, does not have these drawbacks. We can therefore keep all the variables.

The principle of the diagram is to underline the "remarkable" correlations of the correlation matrix, by a solid line (positive correlation) or dotted line (negative correlation).

A strong correlation is not "remarkable" if it is not direct, but caused by the effect of a third variable. Conversely, weak correlations can be "remarkable". For example, if a variable Y depends on several independent variables, the correlations of Y with each of them are weak and yet "remarkable".

## Generalizations

### Sparse PCA

A particular disadvantage of PCA is that the principal components are usually linear combinations of all input variables. [Sparse PCA](https://en.wikipedia.org/wiki/Sparse_PCA) overcomes this disadvantage by finding linear combinations that contain just a few input variables. It extends the classic method of principal component analysis (PCA) for the reduction of dimensionality of data by adding sparsity constraint on the input variables. Several approaches have been proposed, including

- a regression framework,
- a convex relaxation/semidefinite programming framework,
- a generalized power method framework
- an alternating maximization framework
- forward-backward greedy search and exact methods using branch-and-bound techniques,
- Bayesian formulation framework.

The methodological and theoretical developments of Sparse PCA as well as its applications in scientific studies were recently reviewed in a survey paper.

### Nonlinear PCA

![[media/554440dbca85d8138cabb1ba2d9d6bb7404a4a3c.png]]
Linear PCA versus nonlinear Principal Manifolds for [visualization](https://en.wikipedia.org/wiki/Scientific_visualization) of [breast cancer](https://en.wikipedia.org/wiki/Breast_cancer) [microarray](https://en.wikipedia.org/wiki/Microarray) data: a) Configuration of nodes and 2D Principal Surface in the 3D PCA linear manifold. The dataset is curved and cannot be mapped adequately on a 2D principal plane; b) The distribution in the internal 2D non-linear principal surface coordinates (ELMap2D) together with an estimation of the density of points; c) The same as b), but for the linear 2D PCA manifold (PCA2D). The "basal" breast cancer subtype is visualized more adequately with ELMap2D and some features of the distribution become better resolved in comparison to PCA2D. Principal manifolds are produced by the [elastic maps](https://en.wikipedia.org/wiki/Elastic_map) algorithm. Data are available for public competition. Software is available for free non-commercial use.

Most of the modern methods for [nonlinear dimensionality reduction](https://en.wikipedia.org/wiki/Nonlinear_dimensionality_reduction) find their theoretical and algorithmic roots in PCA or K-means. Pearson's original idea was to take a straight line (or plane) which will be "the best fit" to a set of data points. [Trevor Hastie](https://en.wikipedia.org/wiki/Trevor_Hastie) expanded on this concept by proposing **Principal [curves](https://en.wikipedia.org/wiki/Curve)** as the natural extension for the geometric interpretation of PCA, which explicitly constructs a manifold for data [approximation](https://en.wikipedia.org/wiki/Approximation) followed by [projecting](https://en.wikipedia.org/wiki/Projection_(mathematics) "Projection (mathematics)") the points onto it. See also the [elastic map](https://en.wikipedia.org/wiki/Elastic_map) algorithm and [principal geodesic analysis](https://en.wikipedia.org/wiki/Principal_geodesic_analysis). Another popular generalization is [[Kernel PCA]], which corresponds to PCA performed in a reproducing kernel Hilbert space associated with a positive definite kernel.

In [multilinear subspace learning](https://en.wikipedia.org/wiki/Multilinear_subspace_learning), PCA is generalized to [multilinear PCA](https://en.wikipedia.org/wiki/Multilinear_principal_component_analysis) (MPCA) that extracts features directly from tensor representations. MPCA is solved by performing PCA in each mode of the tensor iteratively. MPCA has been applied to face recognition, gait recognition, etc. MPCA is further extended to uncorrelated MPCA, non-negative MPCA and robust MPCA.

*N*-way principal component analysis may be performed with models such as [Tucker decomposition](https://en.wikipedia.org/wiki/Tucker_decomposition), [PARAFAC](https://en.wikipedia.org/wiki/PARAFAC), multiple factor analysis, co-inertia analysis, STATIS, and DISTATIS.

### Robust PCA

While PCA finds the mathematically optimal method (as in minimizing the squared error), it is still sensitive to [outliers](https://en.wikipedia.org/wiki/Outlier) in the data that produce large errors, something that the method tries to avoid in the first place. It is therefore common practice to remove outliers before computing PCA. However, in some contexts, outliers can be difficult to identify. For example, in [data mining](https://en.wikipedia.org/wiki/Data_mining) algorithms like [correlation clustering](https://en.wikipedia.org/wiki/Correlation_clustering), the assignment of points to clusters and outliers is not known beforehand. A recently proposed generalization of PCA based on a weighted PCA increases robustness by assigning different weights to data objects based on their estimated relevancy.

Outlier-resistant variants of PCA have also been proposed, based on L1-norm formulations ([L1-PCA](https://en.wikipedia.org/wiki/L1-norm_principal_component_analysis)).

[Robust principal component analysis](https://en.wikipedia.org/wiki/Robust_principal_component_analysis) (RPCA) via decomposition in low-rank and sparse matrices is a modification of PCA that works well with respect to grossly corrupted observations.

## Similar techniques

### Independent component analysis

[Independent component analysis](https://en.wikipedia.org/wiki/Independent_component_analysis) (ICA) is directed to similar problems as principal component analysis, but finds additively separable components rather than successive approximations.

### Network component analysis

Given a matrix $E$, it tries to decompose it into two matrices such that $E=AP$. A key difference from techniques such as PCA and ICA is that some of the entries of $A$ are constrained to be 0. Here $P$ is termed the regulatory layer. While in general such a decomposition can have multiple solutions, they prove that if the following conditions are satisfied :

1.  $A$ has full column rank
2.  Each column of $A$ must have at least $L-1$ zeroes where $L$ is the number of columns of $A$ (or alternatively the number of rows of $P$). The justification for this criterion is that if a node is removed from the regulatory layer along with all the output nodes connected to it, the result must still be characterized by a connectivity matrix with full column rank.
3.  $P$ must have full row rank.

then the decomposition is unique up to multiplication by a scalar.

### Discriminant analysis of principal components

Discriminant analysis of principal components (DAPC) is a multivariate method used to identify and describe clusters of genetically related individuals. Genetic variation is partitioned into two components: variation between groups and within groups, and it maximizes the former. Linear discriminants are linear combinations of alleles which best separate the clusters. Alleles that most contribute to this discrimination are therefore those that are the most markedly different across groups. The contributions of alleles to the groupings identified by DAPC can allow identifying regions of the genome driving the genetic divergence among groups In DAPC, data are first transformed using a principal components analysis (PCA) and subsequently clusters are identified using discriminant analysis (DA).

A DAPC can be realized on R using the package Adegenet. (more info: [adegenet on the web](https://adegenet.r-forge.r-project.org/))

### Directional component analysis

[Directional component analysis](https://en.wikipedia.org/wiki/Directional_component_analysis) (DCA) is a method used in the atmospheric sciences for analysing multivariate datasets. Like PCA, it allows for dimension reduction, improved visualization and improved interpretability of large data-sets. Also like PCA, it is based on a covariance matrix derived from the input dataset. The difference between PCA and DCA is that DCA additionally requires the input of a vector direction, referred to as the impact. Whereas PCA maximises explained variance, DCA maximises probability density given impact. The motivation for DCA is to find components of a multivariate dataset that are both likely (measured using probability density) and important (measured using the impact). DCA has been used to find the most likely and most serious heat-wave patterns in weather prediction ensembles , and the most likely and most impactful changes in rainfall due to climate change .

## Software/source code

- [ALGLIB](https://en.wikipedia.org/wiki/ALGLIB) – a C++ and C# library that implements PCA and truncated PCA
- [Analytica](https://en.wikipedia.org/wiki/Analytica_(software) "Analytica (software)") – The built-in EigenDecomp function computes principal components.
- [ELKI](https://en.wikipedia.org/wiki/ELKI) – includes PCA for projection, including robust variants of PCA, as well as PCA-based [clustering algorithms](https://en.wikipedia.org/wiki/Cluster_analysis).
- [Gretl](https://en.wikipedia.org/wiki/Gretl) – principal component analysis can be performed either via the `pca` command or via the `princomp()` function.
- [Julia](https://en.wikipedia.org/wiki/Julia_language) – Supports PCA with the `pca` function in the MultivariateStats package.
- [KNIME](https://en.wikipedia.org/wiki/KNIME) – A java based nodal arranging software for Analysis, in this the nodes called PCA, PCA compute, PCA Apply, PCA inverse make it easily.
- [Maple (software)](https://en.wikipedia.org/wiki/Maple_(software) "Maple (software)") – The PCA command is used to perform a principal component analysis on a set of data.
- [Mathematica](https://en.wikipedia.org/wiki/Mathematica) – Implements principal component analysis with the PrincipalComponents command using both covariance and correlation methods.
- [MathPHP](https://github.com/markrogoyski/math-php) – [PHP](https://en.wikipedia.org/wiki/PHP) mathematics library with support for PCA.
- [MATLAB](https://en.wikipedia.org/wiki/MATLAB) – The SVD function is part of the basic system. In the Statistics Toolbox, the functions `princomp` and `pca` (R2012b) give the principal components, while the function `pcares` gives the residuals and reconstructed matrix for a low-rank PCA approximation.
- [Matplotlib](https://en.wikipedia.org/wiki/Matplotlib) – a [Python](https://en.wikipedia.org/wiki/Python_(programming_language) "Python (programming language)") library that has a PCA package in the .mlab module.
- [mlpack](https://en.wikipedia.org/wiki/Mlpack) – Provides an implementation of principal component analysis in [C++](https://en.wikipedia.org/wiki/C%2B%2B).
- [mrmath](https://github.com/mikerabat/mrmath) – A high performance math library for [Delphi](https://en.wikipedia.org/wiki/Delphi_(software) "Delphi (software)") and [FreePascal](https://en.wikipedia.org/wiki/Free_Pascal) can perform PCA; including robust variants.
- [NAG Library](https://en.wikipedia.org/wiki/NAG_Numerical_Library) – Principal components analysis is implemented via the `g03aa` routine (available in both the Fortran versions of the Library).
- [NMath](https://en.wikipedia.org/wiki/NMath) – Proprietary numerical library containing PCA for the [.NET Framework](https://en.wikipedia.org/wiki/.NET_Framework).
- [GNU Octave](https://en.wikipedia.org/wiki/GNU_Octave) – Free software computational environment mostly compatible with MATLAB, the function `princomp` gives the principal component.
- [OpenCV](https://en.wikipedia.org/wiki/OpenCV)
- [Oracle Database](https://en.wikipedia.org/wiki/Oracle_Database) 12c – Implemented via `DBMS_DATA_MINING.SVDS_SCORING_MODE` by specifying setting value `SVDS_SCORING_PCA`.
- [Orange (software)](https://en.wikipedia.org/wiki/Orange_(software) "Orange (software)") – Integrates PCA in its visual programming environment. PCA displays a scree plot (degree of explained variance) where user can interactively select the number of principal components.
- [Origin](https://en.wikipedia.org/wiki/Origin_(data_analysis_software) "Origin (data analysis software)") – Contains PCA in its Pro version.
- [Qlucore](https://en.wikipedia.org/wiki/Qlucore) – Commercial software for analyzing multivariate data with instant response using PCA.
- [R](https://en.wikipedia.org/wiki/R_(programming_language) "R (programming language)") – [Free](https://en.wikipedia.org/wiki/Free_software) statistical package, the functions `princomp` and `prcomp` can be used for principal component analysis; `prcomp` uses [[Singular Value Decomposition]] which generally gives better numerical accuracy. Some packages that implement PCA in R, include, but are not limited to: `ade4`, `vegan`, `ExPosition`, `dimRed`, and `FactoMineR`.
- [SAS](https://en.wikipedia.org/wiki/SAS_(software) "SAS (software)") – Proprietary software; for example, see.
- [scikit-learn](https://en.wikipedia.org/wiki/Scikit-learn) – Python library for machine learning which contains PCA, Probabilistic PCA, Kernel PCA, Sparse PCA and other techniques in the decomposition module.
- [Scilab](https://en.wikipedia.org/wiki/Scilab) – Free and open-source, cross-platform numerical computational package, the function `princomp` computes principal component analysis, the function `pca` computes principal component analysis with standardized variables.
- [SPSS](https://en.wikipedia.org/wiki/SPSS) – Proprietary software most commonly used by social scientists for PCA, factor analysis and associated cluster analysis.
- [Weka](https://en.wikipedia.org/wiki/Weka_(machine_learning)) – Java library for machine learning which contains modules for computing principal components.

## See also

- [Correspondence analysis](https://en.wikipedia.org/wiki/Correspondence_analysis) (for contingency tables)
- [Multiple correspondence analysis](https://en.wikipedia.org/wiki/Multiple_correspondence_analysis) (for qualitative variables)
- [Factor analysis of mixed data](https://en.wikipedia.org/wiki/Factor_analysis_of_mixed_data) (for quantitative **and** qualitative variables)
- [Canonical correlation](https://en.wikipedia.org/wiki/Canonical_correlation)
- [CUR matrix approximation](https://en.wikipedia.org/wiki/CUR_matrix_approximation) (can replace of low-rank SVD approximation)
- [Detrended correspondence analysis](https://en.wikipedia.org/wiki/Detrended_correspondence_analysis)
- [Directional component analysis](https://en.wikipedia.org/wiki/Directional_component_analysis)
- [Dynamic mode decomposition](https://en.wikipedia.org/wiki/Dynamic_mode_decomposition)
- [Eigenface](https://en.wikipedia.org/wiki/Eigenface)
- [Expectation–maximization algorithm](https://en.wikipedia.org/wiki/Expectation%E2%80%93maximization_algorithm)
- [Exploratory factor analysis](https://en.wikiversity.org/wiki/Exploratory_factor_analysis) (Wikiversity)
- [Factorial code](https://en.wikipedia.org/wiki/Factorial_code)
- [Functional principal component analysis](https://en.wikipedia.org/wiki/Functional_principal_component_analysis)
- [Geometric data analysis](https://en.wikipedia.org/wiki/Geometric_data_analysis)
- [Independent component analysis](https://en.wikipedia.org/wiki/Independent_component_analysis)
- [[Kernel PCA]]
- [L1-norm principal component analysis](https://en.wikipedia.org/wiki/L1-norm_principal_component_analysis)
- [Low-rank approximation](https://en.wikipedia.org/wiki/Low-rank_approximation)
- [Matrix decomposition](https://en.wikipedia.org/wiki/Matrix_decomposition)
- [Non-negative matrix factorization](https://en.wikipedia.org/wiki/Non-negative_matrix_factorization)
- [Nonlinear dimensionality reduction](https://en.wikipedia.org/wiki/Nonlinear_dimensionality_reduction)
- [Oja's rule](https://en.wikipedia.org/wiki/Oja%27s_rule)
- [Point distribution model](https://en.wikipedia.org/wiki/Point_distribution_model) (PCA applied to morphometry and computer vision)
- [Principal component analysis](https://en.wikibooks.org/wiki/Statistics/Multivariate_Data_Analysis/Principal_Component_Analysis) (Wikibooks)
- [Principal component regression](https://en.wikipedia.org/wiki/Principal_component_regression)
- [Singular spectrum analysis](https://en.wikipedia.org/wiki/Singular_spectrum_analysis)
- [[Singular Value Decomposition]]
- [Sparse PCA](https://en.wikipedia.org/wiki/Sparse_PCA)
- [Transform coding](https://en.wikipedia.org/wiki/Transform_coding)
- [Weighted least squares](https://en.wikipedia.org/wiki/Weighted_least_squares)

## References

1.  Gewers, Felipe L.; Ferreira, Gustavo R.; Arruda, Henrique F. De; Silva, Filipi N.; Comin, Cesar H.; Amancio, Diego R.; Costa, Luciano Da F. (24 May 2021). ["Principal Component Analysis: A Natural Approach to Data Exploration"](https://dl.acm.org/doi/abs/10.1145/3447755). *ACM Comput. Surv*. **54** (4): 70:1–70:34. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1804.02502](https://arxiv.org/abs/1804.02502). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/3447755](https://doi.org/10.1145%2F3447755).
2.  Jolliffe, Ian T.; Cadima, Jorge (2016-04-13). ["Principal component analysis: a review and recent developments"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4792409). *Philosophical Transactions of the Royal Society A: Mathematical, Physical and Engineering Sciences*. **374** (2065) 20150202. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2016RSPTA.37450202J](https://ui.adsabs.harvard.edu/abs/2016RSPTA.37450202J). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1098/rsta.2015.0202](https://doi.org/10.1098%2Frsta.2015.0202). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [4792409](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4792409). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [26953178](https://pubmed.ncbi.nlm.nih.gov/26953178).
3.  Barnett, T. P. & R. Preisendorfer. (1987). ["Origins and levels of monthly and seasonal forecast skill for United States surface air temperatures determined by canonical correlation analysis"](https://doi.org/10.1175%2F1520-0493%281987%29115%3C1825%3Aoaloma%3E2.0.co%3B2). *Monthly Weather Review*. **115** (9): 1825. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1987MWRv..115.1825B](https://ui.adsabs.harvard.edu/abs/1987MWRv..115.1825B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1175/1520-0493(1987)115<1825:oaloma>2.0.co;2](https://doi.org/10.1175%2F1520-0493%281987%29115%3C1825%3Aoaloma%3E2.0.co%3B2).
4.  Hsu, Daniel; Kakade, Sham M.; Zhang, Tong (2008). *A spectral algorithm for learning hidden markov models*. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0811.4413](https://arxiv.org/abs/0811.4413). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2008arXiv0811.4413H](https://ui.adsabs.harvard.edu/abs/2008arXiv0811.4413H).
5.  ^   Markopoulos, Panos P.; Kundu, Sandipan; Chamadia, Shubham; Pados, Dimitris A. (15 August 2017). "Efficient L1-Norm Principal-Component Analysis via Bit Flipping". *IEEE Transactions on Signal Processing*. **65** (16): 4252–4264. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1610.01959](https://arxiv.org/abs/1610.01959). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2017ITSP...65.4252M](https://ui.adsabs.harvard.edu/abs/2017ITSP...65.4252M). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TSP.2017.2708023](https://doi.org/10.1109%2FTSP.2017.2708023). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [7931130](https://api.semanticscholar.org/CorpusID:7931130).
6.  ^   Chachlakis, Dimitris G.; Prater-Bennette, Ashley; Markopoulos, Panos P. (22 November 2019). ["L1-norm Tucker Tensor Decomposition"](https://doi.org/10.1109%2FACCESS.2019.2955134). *IEEE Access*. **7**: 178454–178465. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1904.06455](https://arxiv.org/abs/1904.06455). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019IEEEA...7q8454C](https://ui.adsabs.harvard.edu/abs/2019IEEEA...7q8454C). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/ACCESS.2019.2955134](https://doi.org/10.1109%2FACCESS.2019.2955134).
7.  ^   Markopoulos, Panos P.; Karystinos, George N.; Pados, Dimitris A. (October 2014). "Optimal Algorithms for L1-subspace Signal Processing". *IEEE Transactions on Signal Processing*. **62** (19): 5046–5058. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1405.6785](https://arxiv.org/abs/1405.6785). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2014ITSP...62.5046M](https://ui.adsabs.harvard.edu/abs/2014ITSP...62.5046M). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TSP.2014.2338077](https://doi.org/10.1109%2FTSP.2014.2338077). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [1494171](https://api.semanticscholar.org/CorpusID:1494171).
8.  Zhan, J.; Vaswani, N. (2015). "Robust PCA With Partial Subspace Knowledge". *IEEE Transactions on Signal Processing*. **63** (13): 3332–3347. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1403.1591](https://arxiv.org/abs/1403.1591). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2015ITSP...63.3332Z](https://ui.adsabs.harvard.edu/abs/2015ITSP...63.3332Z). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/tsp.2015.2421485](https://doi.org/10.1109%2Ftsp.2015.2421485). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [1516440](https://api.semanticscholar.org/CorpusID:1516440).
9.  Kanade, T.; Ke, Qifa (June 2005). "Robust L₁ Norm Factorization in the Presence of Outliers and Missing Data by Alternative Convex Programming". *2005 IEEE Computer Society Conference on Computer Vision and Pattern Recognition (CVPR'05)*. Vol. 1. IEEE. pp. 739–746. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.63.4605](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.63.4605). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/CVPR.2005.309](https://doi.org/10.1109%2FCVPR.2005.309). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-7695-2372-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-7695-2372-9). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [17144854](https://api.semanticscholar.org/CorpusID:17144854).
10. [Pearson, K.](https://en.wikipedia.org/wiki/Karl_Pearson) (1901). ["On Lines and Planes of Closest Fit to Systems of Points in Space"](https://zenodo.org/record/1430636). *Philosophical Magazine*. **2** (11): 559–572. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/14786440109462720](https://doi.org/10.1080%2F14786440109462720). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [125037489](https://api.semanticscholar.org/CorpusID:125037489).
11. Hotelling, H. (1933). Analysis of a complex of statistical variables into principal components. *[Journal of Educational Psychology](https://en.wikipedia.org/wiki/Journal_of_Educational_Psychology)*, **24**, 417–441, and 498–520.  
    Hotelling, H (1936). "Relations between two sets of variates". *[Biometrika](https://en.wikipedia.org/wiki/Biometrika)*. **28** (3/4): 321–377. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2333955](https://doi.org/10.2307%2F2333955). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2333955](https://www.jstor.org/stable/2333955).
12. Stewart, G. W. (1993). ["On the early history of the singular value decomposition"](http://purl.umn.edu/1868). *[SIAM Review](https://en.wikipedia.org/wiki/SIAM_Review)*. **35** (4): 551–566. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1993SIAMR..35..551S](https://ui.adsabs.harvard.edu/abs/1993SIAMR..35..551S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/1035134](https://doi.org/10.1137%2F1035134). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1903/566](https://hdl.handle.net/1903%2F566).
13. ^      Jolliffe, I. T. (2002). [Principal Component Analysis](http://link.springer.com/10.1007/b98835). Springer Series in Statistics. New York: Springer-Verlag. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/b98835](https://doi.org/10.1007%2Fb98835). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95442-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95442-4).
14. ^      Holmes, Mark H. (2023). *Introduction to Scientific Computing and Data Analysis*. Texts in Computational Science and Engineering (2nd ed.). Springer. pp. 475–490. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-031-22429-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-031-22429-4).
15. Forkman J., Josse, J., Piepho, H. P. (2019). ["Hypothesis tests for principal component analysis when variables are standardized"](https://doi.org/10.1007%2Fs13253-019-00355-5). *Journal of Agricultural, Biological, and Environmental Statistics*. **24** (2): 289–308. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2019JABES..24..289F](https://ui.adsabs.harvard.edu/abs/2019JABES..24..289F). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s13253-019-00355-5](https://doi.org/10.1007%2Fs13253-019-00355-5).`{{`[`cite journal`](https://en.wikipedia.org/wiki/Template:Cite_journal)`}}`: CS1 maint: multiple names: authors list ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_multiple_names:_authors_list))
16. Boyd, Stephen; Vandenberghe, Lieven (2004-03-08). *Convex Optimization*. Cambridge University Press. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/cbo9780511804441](https://doi.org/10.1017%2Fcbo9780511804441). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-83378-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-83378-3).
17. [Fukunaga, Keinosuke](https://en.wikipedia.org/wiki/Keinosuke_Fukunaga) (1990). [Introduction to Statistical Pattern Recognition](https://dl.acm.org/doi/book/10.5555/92131). Elsevier. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-12-269851-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-12-269851-4).
18. Alizadeh, Elaheh; Lyons, Samanthe M; Castle, Jordan M; Prasad, Ashok (2016). ["Measuring systematic changes in invasive cancer cell shape using Zernike moments"](https://pubs.rsc.org/en/Content/ArticleLanding/2016/IB/C6IB00100A). *Integrative Biology*. **8** (11): 1183–1193. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1039/C6IB00100A](https://doi.org/10.1039%2FC6IB00100A). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [27735002](https://pubmed.ncbi.nlm.nih.gov/27735002).
19. Leznik, M; Tofallis, C. 2005 [Estimating Invariant Principal Components Using Diagonal Regression.](https://uhra.herts.ac.uk/bitstream/handle/2299/715/S56.pdf)
20. Jonathon Shlens, [A Tutorial on Principal Component Analysis.](https://arxiv.org/abs/1404.1100)
21. ^    Soummer, Rémi; Pueyo, Laurent; Larkin, James (2012). "Detection and Characterization of Exoplanets and Disks Using Projections on Karhunen-Loève Eigenimages". *The Astrophysical Journal Letters*. **755** (2): L28. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1207.4197](https://arxiv.org/abs/1207.4197). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2012ApJ...755L..28S](https://ui.adsabs.harvard.edu/abs/2012ApJ...755L..28S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1088/2041-8205/755/2/L28](https://doi.org/10.1088%2F2041-8205%2F755%2F2%2FL28). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [51088743](https://api.semanticscholar.org/CorpusID:51088743).
22. Pueyo, Laurent (2016). ["Detection and Characterization of Exoplanets using Projections on Karhunen Loeve Eigenimages: Forward Modeling"](https://doi.org/10.3847%2F0004-637X%2F824%2F2%2F117). *The Astrophysical Journal*. **824** (2): 117. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1604.06097](https://arxiv.org/abs/1604.06097). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2016ApJ...824..117P](https://ui.adsabs.harvard.edu/abs/2016ApJ...824..117P). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3847/0004-637X/824/2/117](https://doi.org/10.3847%2F0004-637X%2F824%2F2%2F117). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [118349503](https://api.semanticscholar.org/CorpusID:118349503).
23. ^   Blanton, Michael R.; Roweis, Sam (2007). "K-corrections and filter transformations in the ultraviolet, optical, and near infrared". *The Astronomical Journal*. **133** (2): 734–754. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[astro-ph/0606170](https://arxiv.org/abs/astro-ph/0606170). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2007AJ....133..734B](https://ui.adsabs.harvard.edu/abs/2007AJ....133..734B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1086/510127](https://doi.org/10.1086%2F510127). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [18561804](https://api.semanticscholar.org/CorpusID:18561804).
24. ^    Zhu, Guangtun B. (2016-12-19). "Nonnegative Matrix Factorization (NMF) with Heteroscedastic Uncertainties and Missing data". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1612.06037](https://arxiv.org/abs/1612.06037) \[[astro-ph.IM](https://arxiv.org/archive/astro-ph.IM)\].
25. ^       Ren, Bin; Pueyo, Laurent; Zhu, Guangtun B.; Duchêne, Gaspard (2018). ["Non-negative Matrix Factorization: Robust Extraction of Extended Structures"](https://doi.org/10.3847%2F1538-4357%2Faaa1f2). *The Astrophysical Journal*. **852** (2): 104. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1712.10317](https://arxiv.org/abs/1712.10317). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2018ApJ...852..104R](https://ui.adsabs.harvard.edu/abs/2018ApJ...852..104R). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3847/1538-4357/aaa1f2](https://doi.org/10.3847%2F1538-4357%2Faaa1f2). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [3966513](https://api.semanticscholar.org/CorpusID:3966513).
26. ["What are the Pros and cons of the PCA?"](https://www.i2tutorials.com/what-are-the-pros-and-cons-of-the-pca/). *i2tutorials*. September 1, 2019. Retrieved June 4, 2021.
27. Abbott, Dean (May 2014). *Applied Predictive Analytics*. Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-72796-6](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-72796-6).
28. ^   Jiang, Hong; Eskridge, Kent M. (2000). ["Bias in Principal Components Analysis Due to Correlated Observations"](https://newprairiepress.org/agstatconference/2000/proceedings/13/). *Conference on Applied Statistics in Agriculture*. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.4148/2475-7772.1247](https://doi.org/10.4148%2F2475-7772.1247). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [2475-7772](https://search.worldcat.org/issn/2475-7772).
29. Linsker, Ralph (March 1988). "Self-organization in a perceptual network". *IEEE Computer*. **21** (3): 105–117. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1988Compr..21c.105L](https://ui.adsabs.harvard.edu/abs/1988Compr..21c.105L). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/2.36](https://doi.org/10.1109%2F2.36). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [1527671](https://api.semanticscholar.org/CorpusID:1527671).
30. Deco & Obradovic (1996). [An Information-Theoretic Approach to Neural Computing](https://books.google.com/books?id=z4XTBwAAQBAJ). New York, NY: Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4612-4016-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4612-4016-7).
31. Plumbley, Mark (1991). *Information theory and unsupervised neural networks*.Tech Note
32. Geiger, Bernhard; Kubin, Gernot (January 2013). "Signal Enhancement as Minimization of Relevant Information Loss". *Proc. ITG Conf. On Systems, Communication and Coding*. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1205.6935](https://arxiv.org/abs/1205.6935). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2012arXiv1205.6935G](https://ui.adsabs.harvard.edu/abs/2012arXiv1205.6935G).
33. See also the tutorial [here](http://www.cs.otago.ac.nz/cosc453/student_tutorials/principal_components.pdf)
34. ["Engineering Statistics Handbook Section 6.5.5.2"](http://www.itl.nist.gov/div898/handbook/pmc/section5/pmc552.htm). Retrieved 19 January 2015.
35. A.A. Miranda, Y.-A. Le Borgne, and G. Bontempi. [New Routes from Minimal Approximation Error to Principal Components](http://www.ulb.ac.be/di/map/yleborgn/pub/NPL_PCA_07.pdf), Volume 27, Number 3 / June, 2008, Neural Processing Letters, Springer
37. ["SAS/STAT(R) 9.3 User's Guide"](http://support.sas.com/documentation/cdl/en/statug/63962/HTML/default/viewer.htm#statug_princomp_sect001.htm).
38. [eig function](http://www.mathworks.com/access/helpdesk/help/techdoc/ref/eig.html#998306) Matlab documentation
39. ["Face Recognition System-PCA based"](https://www.mathworks.com/matlabcentral/fileexchange/24634-face-recognition-system-pca-based). *www.mathworks.com*. 19 June 2023.
40. [Eigenvalues function](http://reference.wolfram.com/mathematica/ref/Eigenvalues.html) Mathematica documentation
41. Roweis, Sam. "EM Algorithms for PCA and SPCA." Advances in Neural Information Processing Systems. Ed. Michael I. Jordan, Michael J. Kearns, and [Sara A. Solla](https://en.wikipedia.org/wiki/Sara_A._Solla) The MIT Press, 1998.
42. Geladi, Paul; Kowalski, Bruce (1986). "Partial Least Squares Regression:A Tutorial". *Analytica Chimica Acta*. **185**: 1–17. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1986AcAC..185....1G](https://ui.adsabs.harvard.edu/abs/1986AcAC..185....1G). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0003-2670(86)80028-9](https://doi.org/10.1016%2F0003-2670%2886%2980028-9).
43. Kramer, R. (1998). [Chemometric Techniques for Quantitative Analysis](https://books.google.com/books?id=iBpOzwAOfHYC). New York: CRC Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-203-90980-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-203-90980-5).
44. Andrecut, M. (2009). "Parallel GPU Implementation of Iterative PCA Algorithms". *Journal of Computational Biology*. **16** (11): 1593–1599. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0811.1081](https://arxiv.org/abs/0811.1081). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1089/cmb.2008.0221](https://doi.org/10.1089%2Fcmb.2008.0221). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [19772385](https://pubmed.ncbi.nlm.nih.gov/19772385). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [1362603](https://api.semanticscholar.org/CorpusID:1362603).
45. Warmuth, M. K.; Kuzmin, D. (2008). ["Randomized online PCA algorithms with regret bounds that are logarithmic in the dimension"](http://www.jmlr.org/papers/volume9/warmuth08a/warmuth08a.pdf) (PDF). *Journal of Machine Learning Research*. **9**: 2287–2320.
46. Kaplan, R.M., & Saccuzzo, D.P. (2010). *Psychological Testing: Principles, Applications, and Issues.* (8th ed.). Belmont, CA: Wadsworth, Cengage Learning.
47. Shevky, Eshref; Williams, Marilyn (1949). *The Social Areas of Los Angeles: Analysis and Typology*. University of California Press.
48. Flood, J (2000). Sydney divided: factorial ecology revisited. Paper to the APA Conference 2000, Melbourne, November and to the 24th ANZRSAI Conference, Hobart, December 2000.[1](https://en.wikipedia.org/wiki/1)(https://www.academia.edu/5135339/Sydney_Divided_Factorial_Ecology_Revisited)
49. ["Socio-Economic Indexes for Areas"](https://www.abs.gov.au/websitedbs/censushome.nsf/home/seifa). *Australian Bureau of Statistics*. 2011. Retrieved 2022-05-05.
50. Schamberger, Tamara; Schuberth, Florian; Henseler, Jörg (2023). "Confirmatory composite analysis in human development research". *International Journal of Behavioral Development*. **47** (1): 88–100. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1177/01650254221117506](https://doi.org/10.1177%2F01650254221117506). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[10362/143639](https://hdl.handle.net/10362%2F143639).
51. Human Development Reports. ["Human Development Index"](https://hdr.undp.org/en/content/human-development-index-hdi). *United Nations Development Programme*. Retrieved 2022-05-06.
52. Novembre, John; Stephens, Matthew (2008). ["Interpreting principal component analyses of spatial population genetic variation"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3989108). *Nat Genet*. **40** (5): 646–49. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1038/ng.139](https://doi.org/10.1038%2Fng.139). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [3989108](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3989108). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [18425127](https://pubmed.ncbi.nlm.nih.gov/18425127).
53. [Elhaik, Eran](https://en.wikipedia.org/wiki/Eran_Elhaik) (2022). ["Principal Component Analyses (PCA)‑based findings in population genetic studies are highly biased and must be reevaluated"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9424212). *[Scientific Reports](https://en.wikipedia.org/wiki/Scientific_Reports)*. **12** (1) 14683. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2022NatSR..1214683E](https://ui.adsabs.harvard.edu/abs/2022NatSR..1214683E). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1038/s41598-022-14395-4](https://doi.org/10.1038%2Fs41598-022-14395-4). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [9424212](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9424212). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [36038559](https://pubmed.ncbi.nlm.nih.gov/36038559). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [251932226](https://api.semanticscholar.org/CorpusID:251932226).
54. DeSarbo, Wayne; Hausmann, Robert; Kukitz, Jeffrey (2007). ["Restricted principal components analysis for marketing research"](https://www.researchgate.net/publication/247623679). *Journal of Marketing in Management*. **2**: 305–328 – via ResearchGate.
55. Dutton, William H; Blank, Grant (2013). [Cultures of the Internet: The Internet in Britain](http://oxis.oii.ox.ac.uk/wp-content/uploads/2014/11/OxIS-2013.pdf) (PDF). Oxford Internet Institute. p. 6.
56. Flood, Joe (2008). ["Multinomial Analysis for Housing Careers Survey"](https://www.academia.edu/33218811). *Paper to the European Network for Housing Research Conference, Dublin*. Retrieved 6 May 2022.
57. ^   See Ch. 9 in Michael B. Miller (2013). *Mathematics and Statistics for Financial Risk Management*, 2nd Edition. Wiley [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-75029-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-75029-2)
58. ^   §9.7 in [John Hull](https://en.wikipedia.org/wiki/John_C._Hull_(economist) "John C. Hull (economist)") (2018). *Risk Management and Financial Institutions,* 5th Edition. Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1119448115](https://en.wikipedia.org/wiki/Special:BookSources/1119448115)
59. §III.A.3.7.2 in Carol Alexander and Elizabeth Sheedy, eds. (2004). *The Professional Risk Managers' Handbook*. [PRMIA](https://en.wikipedia.org/wiki/PRMIA). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0976609704](https://en.wikipedia.org/wiki/Special:BookSources/978-0976609704)
60. [example decomposition](https://www-2.rotman.utoronto.ca/~hull/RMFI/PCA_6thEdition_Example.xls), [John Hull](https://en.wikipedia.org/wiki/John_C._Hull_(economist) "John C. Hull (economist)")
61. Libin Yang. [An Application of Principal Component Analysis to Stock Portfolio Management](https://ir.canterbury.ac.nz/bitstream/handle/10092/10293/thesis.pdf?sequence=1). Department of Economics and Finance, [University of Canterbury](https://en.wikipedia.org/wiki/University_of_Canterbury), January 2015.
62. Giorgia Pasini (2017); [Principal Component Analysis for Stock Portfolio Management](https://ijpam.eu/contents/2017-115-1/12/12.pdf). *International Journal of Pure and Applied Mathematics*. Volume 115 No. 1 2017, 153–167
63. ^   See Ch. 25 § "Scenario testing using principal component analysis" in Li Ong (2014). ["A Guide to IMF Stress Testing Methods and Models"](https://www.elibrary.imf.org/display/book/9781484368589/9781484368589.xml), [International Monetary Fund](https://en.wikipedia.org/wiki/International_Monetary_Fund)
64. Chapin, John; Nicolelis, Miguel (1999). "Principal component analysis of neuronal ensemble activity reveals multidimensional somatosensory representations". *Journal of Neuroscience Methods*. **94** (1): 121–140. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0165-0270(99)00130-2](https://doi.org/10.1016%2FS0165-0270%2899%2900130-2). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [10638820](https://pubmed.ncbi.nlm.nih.gov/10638820). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [17786731](https://api.semanticscholar.org/CorpusID:17786731).
65. Brenner, N., Bialek, W., & de Ruyter van Steveninck, R.R. (2000).
66. Jirsa, Victor; Friedrich, R; Haken, Herman; Kelso, Scott (1994). "A theoretical model of phase transitions in the human brain". *Biological Cybernetics*. **71** (1): 27–35. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/bf00198909](https://doi.org/10.1007%2Fbf00198909). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [8054384](https://pubmed.ncbi.nlm.nih.gov/8054384). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [5155075](https://api.semanticscholar.org/CorpusID:5155075).
67. Benzécri, J.-P. (1973). *L'Analyse des Données. Volume II. L'Analyse des Correspondances*. Paris, France: Dunod.
68. Greenacre, Michael (1983). *Theory and Applications of Correspondence Analysis*. London: Academic Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-12-299050-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-12-299050-2).
69. Le Roux; Brigitte and Henry Rouanet (2004). [Geometric Data Analysis, From Correspondence Analysis to Structured Data Analysis](https://books.google.com/books?id=a6bDBUF58XwC). Dordrecht: Kluwer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4020-2235-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4020-2235-7).
70. Timothy A. Brown. [Confirmatory Factor Analysis for Applied Research Methodology in the social sciences](https://books.google.com/books?id=JDb3BQAAQBAJ). Guilford Press, 2006
71. Meglen, R.R. (1991). "Examining Large Databases: A Chemometric Approach Using Principal Component Analysis". *Journal of Chemometrics*. **5** (3): 163–179. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/cem.1180050305](https://doi.org/10.1002%2Fcem.1180050305). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [120886184](https://api.semanticscholar.org/CorpusID:120886184).
72. H. Zha; C. Ding; M. Gu; X. He; H.D. Simon (Dec 2001). ["Spectral Relaxation for K-means Clustering"](http://ranger.uta.edu/~chqding/papers/Zha-Kmeans.pdf) (PDF). *Neural Information Processing Systems Vol.14 (NIPS 2001)*: 1057–1064.
73. Chris Ding; Xiaofeng He (July 2004). ["K-means Clustering via Principal Component Analysis"](http://ranger.uta.edu/~chqding/papers/KmeansPCA1.pdf) (PDF). *Proc. Of Int'l Conf. Machine Learning (ICML 2004)*: 225–232.
74. Drineas, P.; A. Frieze; R. Kannan; S. Vempala; V. Vinay (2004). ["Clustering large graphs via the singular value decomposition"](http://www.cc.gatech.edu/~vempala/papers/dfkvv.pdf) (PDF). *Machine Learning*. **56** (1–3): 9–33. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2004MLear..56....9D](https://ui.adsabs.harvard.edu/abs/2004MLear..56....9D). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1023/b:mach.0000033113.59016.96](https://doi.org/10.1023%2Fb%3Amach.0000033113.59016.96). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [5892850](https://api.semanticscholar.org/CorpusID:5892850). Retrieved 2012-08-02.
75. Cohen, M.; S. Elder; C. Musco; C. Musco; M. Persu (2014). *Dimensionality reduction for k-means clustering and low rank approximation (Appendix B)*. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1410.6801](https://arxiv.org/abs/1410.6801). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2014arXiv1410.6801C](https://ui.adsabs.harvard.edu/abs/2014arXiv1410.6801C).
76. Hui Zou; Trevor Hastie; Robert Tibshirani (2006). ["Sparse principal component analysis"](http://www-stat.stanford.edu/~hastie/Papers/spc_jcgs.pdf) (PDF). *[Journal of Computational and Graphical Statistics](https://en.wikipedia.org/wiki/Journal_of_Computational_and_Graphical_Statistics)*. **15** (2): 262–286. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.62.580](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.62.580). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1198/106186006x113430](https://doi.org/10.1198%2F106186006x113430). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [5730904](https://api.semanticscholar.org/CorpusID:5730904).
77. Alexandre d'Aspremont; Laurent El Ghaoui; Michael I. Jordan; Gert R. G. Lanckriet (2007). ["A Direct Formulation for Sparse PCA Using Semidefinite Programming"](http://www.cmap.polytechnique.fr/~aspremon/PDF/sparsesvd.pdf) (PDF). *[SIAM Review](https://en.wikipedia.org/wiki/SIAM_Review)*. **49** (3): 434–448. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[cs/0406021](https://arxiv.org/abs/cs/0406021). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2007SIAMR..49..434D](https://ui.adsabs.harvard.edu/abs/2007SIAMR..49..434D). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1137/050645506](https://doi.org/10.1137%2F050645506). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [5490061](https://api.semanticscholar.org/CorpusID:5490061).
78. Michel Journee; Yurii Nesterov; Peter Richtarik; Rodolphe Sepulchre (2010). ["Generalized Power Method for Sparse Principal Component Analysis"](http://jmlr.csail.mit.edu/papers/volume11/journee10a/journee10a.pdf) (PDF). *[Journal of Machine Learning Research](https://en.wikipedia.org/wiki/Journal_of_Machine_Learning_Research)*. **11**: 517–553. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0811.4724](https://arxiv.org/abs/0811.4724). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2008arXiv0811.4724J](https://ui.adsabs.harvard.edu/abs/2008arXiv0811.4724J). CORE Discussion Paper 2008/70.
79. Peter Richtarik; Martin Takac; S. Damla Ahipasaoglu (2012). "Alternating Maximization: Unifying Framework for 8 Sparse PCA Formulations and Efficient Parallel Codes". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1212.4137](https://arxiv.org/abs/1212.4137) \[[stat.ML](https://arxiv.org/archive/stat.ML)\].
80. Baback Moghaddam; Yair Weiss; Shai Avidan (2005). ["Spectral Bounds for Sparse PCA: Exact and Greedy Algorithms"](http://books.nips.cc/papers/files/nips18/NIPS2005_0643.pdf) (PDF). *Advances in Neural Information Processing Systems*. Vol. 18. MIT Press.
82. Hui Zou; Lingzhou Xue (2018). ["A Selective Overview of Sparse Principal Component Analysis"](https://doi.org/10.1109%2FJPROC.2018.2846588). *[Proceedings of the IEEE](https://en.wikipedia.org/wiki/Proceedings_of_the_IEEE)*. **106** (8): 1311–1320. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/JPROC.2018.2846588](https://doi.org/10.1109%2FJPROC.2018.2846588).
83. [A. N. Gorban](https://en.wikipedia.org/wiki/Alexander_Nikolaevich_Gorban), A. Y. Zinovyev, ["Principal Graphs and Manifolds"](https://arxiv.org/abs/0809.0490), In: *Handbook of Research on Machine Learning Applications and Trends: Algorithms, Methods and Techniques*, Olivas E.S. et al Eds. Information Science Reference, IGI Global: Hershey, PA, USA, 2009. 28–59.
84. Wang, Y.; Klijn, J. G.; Zhang, Y.; Sieuwerts, A. M.; Look, M. P.; Yang, F.; Talantov, D.; Timmermans, M.; Meijer-van Gelder, M. E.; Yu, J.; et al. (2005). "Gene expression profiles to predict distant metastasis of lymph-node-negative primary breast cancer". *[The Lancet](https://en.wikipedia.org/wiki/The_Lancet)*. **365** (9460): 671–679. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0140-6736(05)17947-1](https://doi.org/10.1016%2FS0140-6736%2805%2917947-1). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [15721472](https://pubmed.ncbi.nlm.nih.gov/15721472). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [16358549](https://api.semanticscholar.org/CorpusID:16358549). [Data online](https://www.ihes.fr/~zinovyev/princmanif2006/)
85. Zinovyev, A. ["ViDaExpert – Multidimensional Data Visualization Tool"](http://bioinfo-out.curie.fr/projects/vidaexpert/). *[Institut Curie](https://en.wikipedia.org/wiki/Curie_Institute_(Paris) "Curie Institute (Paris)")*. Paris. (free for non-commercial use)
86. [Hastie, T.](https://en.wikipedia.org/wiki/Trevor_Hastie); Stuetzle, W. (June 1989). ["Principal Curves"](https://web.stanford.edu/~hastie/Papers/Principal_Curves.pdf) (PDF). *[Journal of the American Statistical Association](https://en.wikipedia.org/wiki/Journal_of_the_American_Statistical_Association)*. **84** (406): 502–506. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1989JASA...84..502H](https://ui.adsabs.harvard.edu/abs/1989JASA...84..502H). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/01621459.1989.10478797](https://doi.org/10.1080%2F01621459.1989.10478797).
87. A.N. Gorban, B. Kegl, D.C. Wunsch, A. Zinovyev (Eds.), [Principal Manifolds for Data Visualisation and Dimension Reduction](https://www.researchgate.net/publication/271642170_Principal_Manifolds_for_Data_Visualisation_and_Dimension_Reduction_LNCSE_58), LNCSE 58, Springer, Berlin – Heidelberg – New York, 2007. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-73749-0](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-73749-0)
88. Vasilescu, M.A.O.; Terzopoulos, D. (2003). [Multilinear Subspace Analysis of Image Ensembles](http://www.cs.toronto.edu/~maov/tensorfaces/cvpr03.pdf) (PDF). Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR'03). Madison, WI.
89. Vasilescu, M.A.O.; Terzopoulos, D. (2002). [Multilinear Analysis of Image Ensembles: TensorFaces](http://www.cs.toronto.edu/~maov/tensorfaces/Springer%20ECCV%202002_files/eccv02proceeding_23500447.pdf) (PDF). Lecture Notes in Computer Science 2350; (Presented at Proc. 7th European Conference on Computer Vision (ECCV'02), Copenhagen, Denmark). Springer, Berlin, Heidelberg. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/3-540-47969-4_30](https://doi.org/10.1007%2F3-540-47969-4_30). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-43745-1](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-43745-1).
90. Vasilescu, M.A.O.; Terzopoulos, D. (June 2005). [Multilinear Independent Component Analysis](http://www.media.mit.edu/~maov/mica/mica05.pdf) (PDF). Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR'05). Vol. 1. San Diego, CA. pp. 547–553.
91. Kirill Simonov, Fedor V. Fomin, Petr A. Golovach, Fahad Panolan (June 9–15, 2019). ["Refined Complexity of PCA with Outliers"](http://proceedings.mlr.press/v97/simonov19a.html). In Kamalika Chaudhuri, Ruslan Salakhutdinov (ed.). *Proceedings of the 36th International Conference on Machine Learning (ICML 2019)*. Vol. 97. Long Beach, California, USA: PMLR. pp. 5818–5826.`{{`[`cite conference`](https://en.wikipedia.org/wiki/Template:Cite_conference)`}}`: CS1 maint: multiple names: authors list ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_multiple_names:_authors_list))
92. Kriegel, H. P.; Kröger, P.; Schubert, E.; Zimek, A. (2008). "A General Framework for Increasing the Robustness of PCA-Based Correlation Clustering Algorithms". *Scientific and Statistical Database Management*. Lecture Notes in Computer Science. Vol. 5069. pp. 418–435. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.144.4864](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.144.4864). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-540-69497-7_27](https://doi.org/10.1007%2F978-3-540-69497-7_27). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-69476-2](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-69476-2).
93. Emmanuel J. Candes; Xiaodong Li; Yi Ma; John Wright (2011). "Robust Principal Component Analysis?". *Journal of the ACM*. **58** (3): 11. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[0912.3599](https://arxiv.org/abs/0912.3599). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/1970392.1970395](https://doi.org/10.1145%2F1970392.1970395). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [7128002](https://api.semanticscholar.org/CorpusID:7128002).
94. T. Bouwmans; E. Zahzah (2014). "Robust PCA via Principal Component Pursuit: A Review for a Comparative Evaluation in Video Surveillance". *Computer Vision and Image Understanding*. **122**: 22–34. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2014CVIU..122...22B](https://ui.adsabs.harvard.edu/abs/2014CVIU..122...22B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.cviu.2013.11.009](https://doi.org/10.1016%2Fj.cviu.2013.11.009).
95. T. Bouwmans; A. Sobral; S. Javed; S. Jung; E. Zahzah (2015). "Decomposition into Low-rank plus Additive Matrices for Background/Foreground Separation: A Review for a Comparative Evaluation with a Large-Scale Dataset". *Computer Science Review*. **23**: 1–71. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1511.01245](https://arxiv.org/abs/1511.01245). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2015arXiv151101245B](https://ui.adsabs.harvard.edu/abs/2015arXiv151101245B). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.cosrev.2016.11.001](https://doi.org/10.1016%2Fj.cosrev.2016.11.001). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [10420698](https://api.semanticscholar.org/CorpusID:10420698).
96. Liao, J. C.; Boscolo, R.; Yang, Y.-L.; Tran, L. M.; [Sabatti, C.](https://en.wikipedia.org/wiki/Chiara_Sabatti); Roychowdhury, V. P. (2003). ["Network component analysis: Reconstruction of regulatory signals in biological systems"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC307600). *Proceedings of the National Academy of Sciences*. **100** (26): 15522–15527. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2003PNAS..10015522L](https://ui.adsabs.harvard.edu/abs/2003PNAS..10015522L). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.2136632100](https://doi.org/10.1073%2Fpnas.2136632100). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [307600](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC307600). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [14673099](https://pubmed.ncbi.nlm.nih.gov/14673099).
97. Liao, T.; Jombart, S.; Devillard, F.; Balloux (2010). ["Discriminant analysis of principal components: a new method for the analysis of genetically structured populations"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2973851). *BMC Genetics*. **11**: 11:94. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1186/1471-2156-11-94](https://doi.org/10.1186%2F1471-2156-11-94). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [2973851](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2973851). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [20950446](https://pubmed.ncbi.nlm.nih.gov/20950446).
98. Jewson, S. (2020). ["An Alternative to PCA for Estimating Dominant Patterns of Climate Variability and Extremes, with Application to U.S. and China Seasonal Rainfall"](https://doi.org/10.3390%2Fatmos11040354). *Atmosphere*. **11** (4): 354. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2020Atmos..11..354J](https://ui.adsabs.harvard.edu/abs/2020Atmos..11..354J). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3390/atmos11040354](https://doi.org/10.3390%2Fatmos11040354). 
99. Scher, S.; Jewson, S.; Messori, G. (2021). ["Robust Worst-Case Scenarios from Ensemble Forecasts"](https://doi.org/10.1175%2FWAF-D-20-0219.1). *Weather and Forecasting*. **36** (4): 1357–1373. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2021WtFor..36.1357S](https://ui.adsabs.harvard.edu/abs/2021WtFor..36.1357S). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1175/WAF-D-20-0219.1](https://doi.org/10.1175%2FWAF-D-20-0219.1). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [236300040](https://api.semanticscholar.org/CorpusID:236300040).
100. Jewson, S.; Messori, G.; Barbato, G.; Mercogliano, P.; Mysiak, J.; Sassi, M. (2022). ["Developing Representative Impact Scenarios From Climate Projection Ensembles, With Application to UKCP18 and EURO-CORDEX Precipitation"](http://urn.kb.se/resolve?urn=urn:nbn:se:uu:diva-492087). *Journal of Advances in Modeling Earth Systems*. **15** (1) e2022MS003038. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1029/2022MS003038](https://doi.org/10.1029%2F2022MS003038). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [254965361](https://api.semanticscholar.org/CorpusID:254965361).
101. ["Principal Components Analysis"](https://stats.idre.ucla.edu/sas/output/principal-components-analysis/). *Institute for Digital Research and Education*. UCLA. Retrieved 29 May 2018.

## Further reading

- Jackson, J.E. (1991). *A User's Guide to Principal Components* (Wiley).
- Jolliffe, I. T. (1986). [Principal Component Analysis](https://archive.org/details/principalcompone00joll_0/page/487). Springer Series in Statistics. Springer-Verlag. pp. [487](https://archive.org/details/principalcompone00joll_0/page/487). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.149.8828](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.149.8828). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/b98835](https://doi.org/10.1007%2Fb98835). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95442-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95442-4).
- Jolliffe, I. T. (2002). [Principal Component Analysis](http://link.springer.com/10.1007/b98835). Springer Series in Statistics. New York: Springer-Verlag. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/b98835](https://doi.org/10.1007%2Fb98835). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-95442-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-95442-4).
- Husson François, Lê Sébastien & Pagès Jérôme (2009). *Exploratory Multivariate Analysis by Example Using R*. Chapman & Hall/CRC The R Series, London. 224p. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-2-7535-0938-2](https://en.wikipedia.org/wiki/Special:BookSources/978-2-7535-0938-2)
- Pagès Jérôme (2014). *[Multiple Factor Analysis by Example Using R](https://books.google.com/books?id=_RIeBQAAQBAJ&q=%22principal+component+analysis%22)*. Chapman & Hall/CRC The R Series London 272 p

## External links

- [University of Copenhagen video by Rasmus Bro](https://www.youtube.com/watch?v=UUxIXU_Ob6E) on [YouTube](https://en.wikipedia.org/wiki/YouTube_video_(identifier))
- [Stanford University video by Andrew Ng](https://www.youtube.com/watch?v=ey2PE5xi9-A#t=2385) on [YouTube](https://en.wikipedia.org/wiki/YouTube_video_(identifier))
- [A Tutorial on Principal Component Analysis](https://arxiv.org/abs/1404.1100)
- [A layman's introduction to principal component analysis](https://www.youtube.com/watch?v=BfTMmoDFXyE) on [YouTube](https://en.wikipedia.org/wiki/YouTube_video_(identifier)) (a video of less than 100 seconds.)
- [StatQuest: StatQuest: Principal Component Analysis (PCA), Step-by-Step](https://www.youtube.com/watch?v=FgakZw6K1QQ) on [YouTube](https://en.wikipedia.org/wiki/YouTube_video_(identifier))
- [Layman's explanation in making sense of principal component analysis, eigenvectors & eigenvalues](https://stats.stackexchange.com/a/140579) on [Stack Overflow](https://en.wikipedia.org/wiki/Stack_Overflow)
- See also the list of [Software implementations](#Software/source_code)
