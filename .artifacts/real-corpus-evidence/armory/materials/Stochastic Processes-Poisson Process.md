[[stochastic-processes.base]]

> Source: [Poisson point process](https://en.wikipedia.org/wiki/Poisson_point_process)
> License: Wikipedia content is available under CC BY-SA 4.0.

<table class="infobox infobox-table ib-prob-dist">

Poisson Process

&#10;

Probability density function
![[media/b7f4eab1426e58f758895276d35c5cccbc286a40.png]]

[Mean](https://en.wikipedia.org/wiki/Expected_value)
$a_{0,t}=\int _{0}^{t}\lambda (\alpha )d\alpha$

[Variance](https://en.wikipedia.org/wiki/Covariance_matrix)
<p>$a_{0,t}+(a_{0,t})^{2}-(a_{0,t})^{2}=a_{0,t}$<br />
since $R_{x}(t_{1},t_{2})=a_{0,min(t_{1},t_{2})}+a_{0,t_{1}}a_{0,t_{2}}$</p>
where for $E\{X^{2}\}=R_{x}(t,t)=a_{0,t}+(a_{0,t})^{2}$

</table>

![[media/0ef5866aa2d3005125f26c75cc68f88199aa9e23.png]]
A visual depiction of a Poisson point process starting

In [probability theory](https://en.wikipedia.org/wiki/Probability_theory), [statistics](https://en.wikipedia.org/wiki/Statistics) and related fields, a **Poisson point process** (also known as: **Poisson random measure**, **Poisson random point field** and **Poisson point field**) is a type of [mathematical object](https://en.wikipedia.org/wiki/Mathematical_object) that consists of [points](https://en.wikipedia.org/wiki/Point_(geometry) "Point (geometry)") randomly located on a [mathematical space](https://en.wikipedia.org/wiki/Space_(mathematics) "Space (mathematics)") with the essential feature that the points occur independently of one another. The process's name derives from the fact that the number of points in any given finite region follows a [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution). The process and the distribution are named after French mathematician [Siméon Denis Poisson](https://en.wikipedia.org/wiki/Sim%C3%A9on_Denis_Poisson). The process itself was discovered independently and repeatedly in several settings, including experiments on [radioactive decay](https://en.wikipedia.org/wiki/Radioactive_decay), telephone call arrivals and [actuarial science](https://en.wikipedia.org/wiki/Actuarial_science).

This point process is used as a [mathematical model](https://en.wikipedia.org/wiki/Mathematical_model) for seemingly random processes in numerous disciplines including [astronomy](https://en.wikipedia.org/wiki/Astronomy), [biology](https://en.wikipedia.org/wiki/Biology), [ecology](https://en.wikipedia.org/wiki/Ecology), [geology](https://en.wikipedia.org/wiki/Geology), [seismology](https://en.wikipedia.org/wiki/Seismology), [physics](https://en.wikipedia.org/wiki/Physics), [economics](https://en.wikipedia.org/wiki/Economics), [image processing](https://en.wikipedia.org/wiki/Image_processing), and [telecommunications](https://en.wikipedia.org/wiki/Telecommunications).

The Poisson point process is often defined on the real number line, where it can be considered a [stochastic process](https://en.wikipedia.org/wiki/Stochastic_process). It is used, for example, in [queueing theory](https://en.wikipedia.org/wiki/Queueing_theory) to model random events distributed in time, such as the arrival of customers at a store, phone calls at an exchange or occurrence of earthquakes. In the [plane](https://en.wikipedia.org/wiki/Plane_(geometry)), the point process, also known as a **spatial Poisson process**, can represent the locations of scattered objects such as transmitters in a [wireless network](https://en.wikipedia.org/wiki/Wireless_network), [particles](https://en.wikipedia.org/wiki/Particles) colliding into a detector or trees in a forest. The process is often used in mathematical models and in the related fields of spatial point processes, [stochastic geometry](https://en.wikipedia.org/wiki/Stochastic_geometry), [spatial statistics](https://en.wikipedia.org/wiki/Spatial_statistics) and [continuum percolation theory](https://en.wikipedia.org/wiki/Continuum_percolation_theory).

The point process depends on a single mathematical object, which, depending on the context, may be a [constant](https://en.wikipedia.org/wiki/Constant_(mathematics) "Constant (mathematics)"), a [locally integrable function](https://en.wikipedia.org/wiki/Locally_integrable_function) or, in more general settings, a [Radon measure](https://en.wikipedia.org/wiki/Radon_measure). In the first case, the constant, known as the **rate** or **intensity**, is the average [density](https://en.wikipedia.org/wiki/Density) of the points in the Poisson process located in some region of space. The resulting point process is called a **homogeneous** or **stationary Poisson point process**. In the second case, the point process is called an **inhomogeneous** or **nonhomogeneous** **Poisson point process**, and the average density of points depend on the location of the underlying space of the Poisson point process. The word *point* is often omitted, but there are other *Poisson processes* of objects, which, instead of points, consist of more complicated mathematical objects such as [lines](https://en.wikipedia.org/wiki/Line_(geometry) "Line (geometry)") and [polygons](https://en.wikipedia.org/wiki/Polygon), and such processes can be based on the Poisson point process. Both the homogeneous and nonhomogeneous Poisson point processes are particular cases of the [generalized renewal process](https://en.wikipedia.org/wiki/Generalized_renewal_process).

## Overview of definitions

Depending on the setting, the process has several equivalent definitions as well as definitions of varying generality owing to its many applications and characterizations. The Poisson point process can be defined, studied and used in one dimension, for example, on the real line, where it can be interpreted as a counting process or part of a queueing model; in higher dimensions such as the plane where it plays a role in [stochastic geometry](https://en.wikipedia.org/wiki/Stochastic_geometry) and [spatial statistics](https://en.wikipedia.org/wiki/Spatial_statistics); or on more general mathematical spaces. Consequently, the notation, terminology and level of mathematical rigour used to define and study the Poisson point process and points processes in general vary according to the context.

Despite all this, the Poisson point process has two key properties—the Poisson property and the independence property— that play an essential role in all settings where the Poisson point process is used. The two properties are not logically independent; indeed, the Poisson distribution of point counts implies the independence property, while in the converse direction the assumptions that: (i) the point process is simple, (ii) has no fixed atoms, and (iii) is a.s. boundedly finite are required.

### Poisson distribution of point counts

A Poisson point process is characterized via the [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution). The Poisson distribution is the probability distribution of a [random variable](https://en.wikipedia.org/wiki/Random_variable) $N$ (called a *Poisson random variable*) such that the probability that $\textstyle N$ equals $\textstyle n$ is given by:

$\Pr\{N=n\}={\frac {\Lambda ^{n}}{n!}}e^{-\Lambda }$

where $n!$ denotes [factorial](https://en.wikipedia.org/wiki/Factorial) and the parameter $\Lambda$ determines the shape of the distribution. (In fact, $\Lambda$ equals the expected value of $N$.)

By definition, a Poisson point process has the property that the number of points in a bounded region of the process's underlying space is a Poisson-distributed random variable.

### Complete independence

Consider a collection of [disjoint](https://en.wikipedia.org/wiki/Disjoint_sets) and bounded subregions of the underlying space. By definition, the number of points of a Poisson point process in each bounded subregion will be completely independent of all the others.

This property is known under several names such as *complete randomness*, *complete independence*, or *independent scattering* and is common to all Poisson point processes. In other words, there is a lack of interaction between different regions and the points in general, which motivates the Poisson process being sometimes called a *purely* or *completely* random process.

## Homogeneous Poisson point process

If a Poisson point process has a parameter of the form $\Lambda =\nu \lambda$, where $\nu$ is Lebesgue measure (that is, it assigns length, area, or volume to sets) and $\lambda$ is a constant, then the point process is called a homogeneous or stationary Poisson point process. The parameter, called **rate** or **intensity**, is related to the expected (or average) number of Poisson points existing in some bounded region, where *rate* is usually used when the underlying space has one dimension. The parameter $\lambda$ can be interpreted as the average number of points per some unit of extent such as [length](https://en.wikipedia.org/wiki/Length), area, [volume](https://en.wikipedia.org/wiki/Volume), or time, depending on the underlying mathematical space, and it is also called the *mean density* or *mean rate*; see [Terminology](#Terminology).

### Interpreted as a counting process

The homogeneous Poisson point process, when considered on the positive half-line, can be defined as a [counting process](https://en.wikipedia.org/wiki/Counting_process), a type of stochastic process, which can be denoted as $\{N(t),t\geq 0\}$. A counting process represents the total number of occurrences or events that have happened up to and including time $t$. A counting process is a homogeneous Poisson counting process with rate $\lambda >0$ if it has the following three properties:

- $N(0)=0;$
- has [independent increments](https://en.wikipedia.org/wiki/Independent_increments); and
- the number of events (or points) in any interval of length $t$ is a Poisson random variable with parameter (or mean) $\lambda t$.

The last property implies:

$\operatorname {E} [N(t)]=\lambda t.$

In other words, the probability of the random variable $N(t)$ being equal to $n$ is given by:

$\Pr\{N(t)=n\}={\frac {(\lambda t)^{n}}{n!}}e^{-\lambda t}.$

The Poisson counting process can also be defined by stating that the time differences between events of the counting process are exponential variables with mean $1/\lambda$. The time differences between the events or arrivals are known as **interarrival**  or **interoccurrence** times.

### Interpreted as a point process on the real line

Interpreted as a [point process](https://en.wikipedia.org/wiki/Point_process), a Poisson point process can be defined on the [real line](https://en.wikipedia.org/wiki/Real_line) by considering the number of points of the process in the interval $(a,b]$. For the homogeneous Poisson point process on the real line with parameter $\lambda >0$, the probability of this random number of points, written here as $N(a,b]$, being equal to some [counting number](https://en.wikipedia.org/wiki/Counting_number) $n$ is given by:

$\Pr\{N(a,b]=n\}={\frac {[\lambda (b-a)]^{n}}{n!}}e^{-\lambda (b-a)},$

For some positive integer $k$, the homogeneous Poisson point process has the finite-dimensional distribution given by:

$\Pr\{N(a_{i},b_{i}]=n_{i},i=1,\dots ,k\}=\prod _{i=1}^{k}{\frac {[\lambda (b_{i}-a_{i})]^{n_{i}}}{n_{i}!}}e^{-\lambda (b_{i}-a_{i})},$

where the real numbers $a_{i}<b_{i}\leq a_{i+1}$.

In other words, $N(a,b]$ is a Poisson random variable with mean $\lambda (b-a)$, where $a\leq b$. Furthermore, the number of points in any two disjoint intervals, say, $(a_{1},b_{1}]$ and $(a_{2},b_{2}]$ are independent of each other, and this extends to any finite number of disjoint intervals. In the queueing theory context, one can consider a point existing (in an interval) as an *event*, but this is different to the word [event](https://en.wikipedia.org/wiki/Event_(probability_theory) "Event (probability theory)") in the probability theory sense. It follows that $\lambda$ is the expected number of *arrivals* that occur per unit of time.

#### Key properties

The previous definition has two important features shared by Poisson point processes in general:

- the number of arrivals in each finite interval has a Poisson distribution;
- the number of arrivals in disjoint intervals are independent random variables.

Furthermore, it has a third feature related to just the homogeneous Poisson point process:

- the Poisson distribution of the number of arrivals in each interval $(a+t,b+t]$ only depends on the interval's length $b-a$.

In other words, for any finite $t>0$, the random variable $N(a+t,b+t]$ is independent of $t$, so it is also called a stationary Poisson process.

#### Law of large numbers

The quantity $\lambda (b_{i}-a_{i})$ can be interpreted as the expected or average number of points occurring in the interval $(a_{i},b_{i}]$, namely:

$\operatorname {E} [N(a_{i},b_{i})]=\lambda (b_{i}-a_{i}),$

where $\operatorname {E}$ denotes the [expectation](https://en.wikipedia.org/wiki/Expected_value) operator. In other words, the parameter $\lambda$ of the Poisson process coincides with the *density* of points. Furthermore, the homogeneous Poisson point process adheres to its own form of the (strong) law of large numbers. More specifically, with probability one:

$\lim _{t\rightarrow \infty }{\frac {N(t)}{t}}=\lambda ,$

where $\lim$ denotes the [limit](https://en.wikipedia.org/wiki/Limit_(mathematics) "Limit (mathematics)") of a function, and $\lambda$ is expected number of arrivals occurred per unit of time.

#### Memoryless property

The distance between two consecutive points of a point process on the real line will be an [exponential random variable](https://en.wikipedia.org/wiki/Exponential_random_variable) with parameter $\lambda$ (or equivalently, mean $1/\lambda$). This implies that the points have the [memoryless](https://en.wikipedia.org/wiki/Memorylessness) property: the existence of one point existing in a finite interval does not affect the probability (distribution) of other points existing, but this property has no natural equivalence when the Poisson process is defined on a space with higher dimensions.

#### Orderliness and simplicity

A point process with [stationary increments](https://en.wikipedia.org/wiki/Stationary_increments) is sometimes said to be *orderly* or *regular* if:

$\Pr\{N(t,t+\delta ]>1\}=o(\delta ),$

where [little-o notation](https://en.wikipedia.org/wiki/Little-o_notation) is being used. A point process is called a **simple point process** when the probability of any of its two points coinciding in the same position, on the underlying space, is zero. For point processes in general on the real line, the property of orderliness implies that the process is simple, which is the case for the homogeneous Poisson point process.

#### Martingale characterization

On the real line, the homogeneous Poisson point process has a connection to the theory of [martingales](https://en.wikipedia.org/wiki/Martingale_(probability_theory) "Martingale (probability theory)") via the following characterization: a point process is the homogeneous Poisson point process if and only if

$N(-\infty ,t]-\lambda t,$

is a martingale.

#### Relationship to other processes

On the real line, the Poisson process is a type of continuous-time [Markov process](https://en.wikipedia.org/wiki/Markov_process) known as a [birth process](https://en.wikipedia.org/wiki/Birth_process), a special case of the [birth–death process](https://en.wikipedia.org/wiki/Birth%E2%80%93death_process) (with just births and zero deaths). More complicated processes with the [Markov property](https://en.wikipedia.org/wiki/Markov_property), such as [Markov arrival processes](https://en.wikipedia.org/wiki/Markov_arrival_process), have been defined where the Poisson process is a special case.

#### Restricted to the half-line

If the homogeneous Poisson process is considered just on the half-line $[0,\infty )$, which can be the case when $t$ represents time then the resulting process is not truly invariant under translation. In that case the Poisson process is no longer stationary, according to some definitions of stationarity.

#### Applications

There have been many applications of the homogeneous Poisson process on the real line in an attempt to model seemingly random and independent events occurring. It has a fundamental role in [queueing theory](https://en.wikipedia.org/wiki/Queueing_theory), which is the probability field of developing suitable stochastic models to represent the random arrival and departure of certain phenomena. For example, customers arriving and being served or phone calls arriving at a phone exchange can be both studied with techniques from queueing theory.

#### Generalizations

The homogeneous Poisson process on the real line is considered one of the simplest stochastic processes for counting random numbers of points. This process can be generalized in a number of ways. One possible generalization is to extend the distribution of interarrival times from the exponential distribution to other distributions, which introduces the stochastic process known as a [renewal process](https://en.wikipedia.org/wiki/Renewal_process). Another generalization is to define the Poisson point process on higher dimensional spaces such as the plane.

### Spatial Poisson point process

A **spatial Poisson process** is a Poisson point process defined in the plane $\textstyle \mathbb {R} ^{2}$. For its mathematical definition, one first considers a bounded, open or closed (or more precisely, [Borel measurable](https://en.wikipedia.org/wiki/Borel_measurable)) region $B$ of the plane. The number of points of a point process $\textstyle N$ existing in this region $\textstyle B\subset \mathbb {R} ^{2}$ is a random variable, denoted by $\textstyle N(B)$. If the points belong to a homogeneous Poisson process with parameter $\textstyle \lambda >0$, then the probability of $\textstyle n$ points existing in $\textstyle B$ is given by:

$\Pr\{N(B)=n\}={\frac {(\lambda |B|)^{n}}{n!}}e^{-\lambda |B|}$

where $\textstyle |B|$ denotes the area of $\textstyle B$.

For some finite integer $\textstyle k\geq 1$, we can give the finite-dimensional distribution of the homogeneous Poisson point process by first considering a collection of disjoint, bounded Borel (measurable) sets $\textstyle B_{1},\dots ,B_{k}$. The number of points of the point process $\textstyle N$ existing in $\textstyle B_{i}$ can be written as $\textstyle N(B_{i})$. Then the homogeneous Poisson point process with parameter $\textstyle \lambda >0$ has the finite-dimensional distribution:

$\Pr\{N(B_{i})=n_{i},i=1,\dots ,k\}=\prod _{i=1}^{k}{\frac {(\lambda |B_{i}|)^{n_{i}}}{n_{i}!}}e^{-\lambda |B_{i}|}.$

#### Applications

![[media/f6cc96064e709aea13faad96d8085a42a81fceb9.jpg]]
According to one statistical study, the positions of cellular or mobile phone base stations in the Australian city [Sydney](https://en.wikipedia.org/wiki/Sydney), pictured above, resemble a realization of a homogeneous Poisson point process, while in many other cities around the world they do not and other point processes are required.

The spatial Poisson point process features prominently in [spatial statistics](https://en.wikipedia.org/wiki/Spatial_statistics), [stochastic geometry](https://en.wikipedia.org/wiki/Stochastic_geometry), and [continuum percolation theory](https://en.wikipedia.org/wiki/Continuum_percolation_theory). This point process is applied in various physical sciences such as a model developed for alpha particles being detected. In recent years, it has been frequently used to model seemingly disordered spatial configurations of certain wireless communication networks. For example, models for cellular or mobile phone networks have been developed where it is assumed the phone network transmitters, known as base stations, are positioned according to a homogeneous Poisson point process.

### Defined in higher dimensions

The previous homogeneous Poisson point process immediately extends to higher dimensions by replacing the notion of area with (high dimensional) volume. For some bounded region $\textstyle B$ of Euclidean space $\textstyle \mathbb {R} ^{d}$, if the points form a homogeneous Poisson process with parameter $\textstyle \lambda >0$, then the probability of $\textstyle n$ points existing in $\textstyle B\subset \mathbb {R} ^{d}$ is given by:

$\Pr\{N(B)=n\}={\frac {(\lambda |B|)^{n}}{n!}}e^{-\lambda |B|}$

where $\textstyle |B|$ now denotes the $\textstyle d$-dimensional volume of $\textstyle B$. Furthermore, for a collection of disjoint, bounded Borel sets $\textstyle B_{1},\dots ,B_{k}\subset \mathbb {R} ^{d}$, let $\textstyle N(B_{i})$ denote the number of points of $\textstyle N$ existing in $\textstyle B_{i}$. Then the corresponding homogeneous Poisson point process with parameter $\textstyle \lambda >0$ has the finite-dimensional distribution:

$\Pr\{N(B_{i})=n_{i},i=1,\dots ,k\}=\prod _{i=1}^{k}{\frac {(\lambda |B_{i}|)^{n_{i}}}{n_{i}!}}e^{-\lambda |B_{i}|}.$

Homogeneous Poisson point processes do not depend on the position of the underlying space through its parameter $\textstyle \lambda$, which implies it is both a stationary process (invariant to translation) and an isotropic (invariant to rotation) stochastic process. Similarly to the one-dimensional case, the homogeneous point process is restricted to some bounded subset of $\mathbb {R} ^{d}$, then depending on some definitions of stationarity, the process is no longer stationary.

### Points are uniformly distributed

If the homogeneous point process is defined on the real line as a mathematical model for occurrences of some phenomenon, then it has the characteristic that the positions of these occurrences or events on the real line (often interpreted as time) will be uniformly distributed. More specifically, if an event occurs (according to this process) in an interval $\textstyle (a,b]$ where $\textstyle a\leq b$, then its location will be a uniform random variable defined on that interval. Furthermore, the homogeneous point process is sometimes called the *uniform* Poisson point process (see [Terminology](#Terminology)). This uniformity property extends to higher dimensions in the Cartesian coordinate, but not in, for example, polar coordinates.

## Inhomogeneous Poisson point process

![[media/acbc5503db3bb9be747e4973e008b49b4f1fc153.png]]
Graph of an inhomogeneous Poisson point process on the real line. The events are marked with black crosses, the time-dependent rate $\lambda (t)$ is given by the function marked red.

The **inhomogeneous** or **nonhomogeneous** **Poisson point process** (see [Terminology](#Terminology)) is a Poisson point process with a Poisson parameter set as some location-dependent function in the underlying space on which the Poisson process is defined. For Euclidean space $\textstyle \mathbb {R} ^{d}$, this is achieved by introducing a locally integrable positive function $\lambda \colon \mathbb {R} ^{d}\to [0,\infty )$, such that for every bounded region $\textstyle B$ the ($\textstyle d$-dimensional) volume integral of $\textstyle \lambda (x)$ over region $\textstyle B$ is finite. In other words, if this integral, denoted by $\textstyle \Lambda (B)$, is:

$\Lambda (B)=\int _{B}\lambda (x)\,\mathrm {d} x<\infty ,$

where $\textstyle {\mathrm {d} x}$ is a ($\textstyle d$-dimensional) volume element, then for every collection of disjoint bounded [Borel measurable](https://en.wikipedia.org/wiki/Borel_measurable) sets $\textstyle B_{1},\dots ,B_{k}$, an inhomogeneous Poisson process with (intensity) function $\textstyle \lambda (x)$ has the finite-dimensional distribution:

$\Pr\{N(B_{i})=n_{i},i=1,\dots ,k\}=\prod _{i=1}^{k}{\frac {(\Lambda (B_{i}))^{n_{i}}}{n_{i}!}}e^{-\Lambda (B_{i})}.$

Furthermore, $\textstyle \Lambda (B)$ has the interpretation of being the expected number of points of the Poisson process located in the bounded region $\textstyle B$, namely

$\Lambda (B)=\operatorname {E} [N(B)].$

### Defined on the real line

On the real line, the inhomogeneous or non-homogeneous Poisson point process has mean measure given by a one-dimensional integral. For two real numbers $\textstyle a$ and $\textstyle b$, where $\textstyle a\leq b$, denote by $\textstyle N(a,b]$ the number points of an inhomogeneous Poisson process with intensity function $\textstyle \lambda (t)$ occurring in the interval $\textstyle (a,b]$. The probability of $\textstyle n$ points existing in the above interval $\textstyle (a,b]$ is given by:

$\Pr\{N(a,b]=n\}={\frac {[\Lambda (a,b)]^{n}}{n!}}e^{-\Lambda (a,b)}.$

where the mean or intensity measure is:

$\Lambda (a,b)=\int _{a}^{b}\lambda (t)\,\mathrm {d} t,$

which means that the random variable $\textstyle N(a,b]$ is a Poisson random variable with mean $\textstyle \operatorname {E} [N(a,b]]=\Lambda (a,b)$.

A feature of the one-dimension setting, is that an inhomogeneous Poisson process can be transformed into a homogeneous by a [monotone transformation](https://en.wikipedia.org/wiki/Monotonic_function) or mapping, which is achieved with the inverse of $\textstyle \Lambda$.

#### Counting process interpretation

The inhomogeneous Poisson point process, when considered on the positive half-line, is also sometimes defined as a counting process. With this interpretation, the process, which is sometimes written as $\textstyle \{N(t),t\geq 0\}$, represents the total number of occurrences or events that have happened up to and including time $\textstyle t$. A counting process is said to be an inhomogeneous Poisson counting process if it has the four properties:

- $\textstyle N(0)=0;$
- has [independent increments](https://en.wikipedia.org/wiki/Independent_increments);
- $\textstyle \Pr\{N(t+h)-N(t)=1\}=\lambda (t)h+o(h);$ and
- $\textstyle \Pr\{N(t+h)-N(t)\geq 2\}=o(h),$

where $\textstyle o(h)$ is asymptotic or [little-o notation](https://en.wikipedia.org/wiki/Little-o_notation) for $\textstyle o(h)/h\rightarrow 0$ as $\textstyle h\rightarrow 0$. In the case of point processes with refractoriness (e.g., neural spike trains) a stronger version of property 4 applies: $\Pr\{N(t+h)-N(t)\geq 2\}=o(h^{2})$.

The above properties imply that $\textstyle N(t+h)-N(t)$ is a Poisson random variable with the parameter (or mean)

$\operatorname {E} [N(t+h)-N(t)]=\int _{t}^{t+h}\lambda (s)\,ds,$

which implies

$\operatorname {E} [N(h)]=\int _{0}^{h}\lambda (s)\,ds.$

### Spatial Poisson process

An inhomogeneous Poisson process defined in the plane $\textstyle \mathbb {R} ^{2}$ is called a **spatial Poisson process** It is defined with intensity function and its intensity measure is obtained performing a surface integral of its intensity function over some region. For example, its intensity function (as a function of Cartesian coordinates $x$ and $\textstyle y$) can be

$\lambda (x,y)=e^{-(x^{2}+y^{2})},$

so the corresponding intensity measure is given by the surface integral

$\Lambda (B)=\int _{B}e^{-(x^{2}+y^{2})}\,\mathrm {d} x\,\mathrm {d} y,$

where $B$ is some bounded region in the plane $\mathbb {R} ^{2}$.

### In higher dimensions

In the plane, $\Lambda (B)$ corresponds to a surface integral while in $\mathbb {R} ^{d}$ the integral becomes a ($d$-dimensional) volume integral.

### Applications

When the real line is interpreted as time, the inhomogeneous process is used in the fields of counting processes and in queueing theory. Examples of phenomena which have been represented by or appear as an inhomogeneous Poisson point process include:

- Goals being scored in a soccer game.
- Defects in a circuit board

In the plane, the Poisson point process is important in the related disciplines of stochastic geometry and spatial statistics. The intensity measure of this point process is dependent on the location of underlying space, which means it can be used to model phenomena with a density that varies over some region. In other words, the phenomena can be represented as points that have a location-dependent density. This processes has been used in various disciplines and uses include the study of salmon and sea lice in the oceans, forestry, and search problems.

### Interpretation of the intensity function

The Poisson intensity function $\lambda (x)$ has an interpretation, considered intuitive, with the volume element $\mathrm {d} x$ in the infinitesimal sense: $\lambda (x)\,\mathrm {d} x$ is the infinitesimal probability of a point of a Poisson point process existing in a region of space with volume $\mathrm {d} x$ located at $x$.

For example, given a homogeneous Poisson point process on the real line, the probability of finding a single point of the process in a small interval of width $\delta$ is approximately $\lambda \delta$. In fact, such intuition is how the Poisson point process is sometimes introduced and its distribution derived.

### Simple point process

If a Poisson point process has an intensity measure that is a locally finite and diffuse (or non-atomic), then it is a **simple point process**. For a simple point process, the probability of a point existing at a single point or location in the underlying (state) space is either zero or one. This implies that, with probability one, no two (or more) points of a Poisson point process coincide in location in the underlying space.

## Simulation

Simulating a Poisson point process on a computer is usually done in a bounded region of space, known as a simulation *window*, and requires two steps: appropriately creating a random number of points and then suitably placing the points in a random manner. Both these two steps depend on the specific Poisson point process that is being simulated.

### Step 1: Number of points

The number of points $N$ in the window, denoted here by $W$, needs to be simulated, which is done by using a (pseudo)-[random number generating](https://en.wikipedia.org/wiki/Random_number_generator) function capable of simulating Poisson random variables.

#### Homogeneous case

For the homogeneous case with the constant $\lambda$, the mean of the Poisson random variable $N$ is set to $\lambda |W|$ where $|W|$ is the length, area or ($d$-dimensional) volume of $W$.

#### Inhomogeneous case

For the inhomogeneous case, $\lambda |W|$ is replaced with the ($d$-dimensional) volume integral

$\Lambda (W)=\int _{W}\lambda (x)\,\mathrm {d} x$

### Step 2: Positioning of points

The second stage requires randomly placing the $\textstyle N$ points in the window $\textstyle W$.

#### Homogeneous case

For the homogeneous case in one dimension, all points are uniformly and independently placed in the window or interval $\textstyle W$. For higher dimensions in a Cartesian coordinate system, each coordinate is uniformly and independently placed in the window $\textstyle W$. If the window is not a subspace of Cartesian space (for example, inside a unit sphere or on the surface of a unit sphere), then the points will not be uniformly placed in $\textstyle W$, and suitable change of coordinates (from Cartesian) are needed.

#### Inhomogeneous (heterogeneous) case

For the inhomogeneous case, a couple of different methods can be used depending on the nature of the intensity function $\textstyle \lambda (x)$. If the intensity function is sufficiently simple, then independent and random non-uniform (Cartesian or other) coordinates of the points can be generated. For example, simulating a Poisson point process on a circular window can be done for an isotropic intensity function (in polar coordinates $\textstyle r$ and $\textstyle \theta$), implying it is rotationally variant or independent of $\textstyle \theta$ but dependent on $\textstyle r$, by a change of variable in $\textstyle r$ if the intensity function is sufficiently simple.

For more complicated intensity functions, one can use an [acceptance-rejection method](https://en.wikipedia.org/wiki/Rejection_sampling), which consists of using (or 'accepting') only certain random points and not using (or 'rejecting') the other points, based on the ratio:.

${\frac {\lambda (x_{i})}{\Lambda (W)}}={\frac {\lambda (x_{i})}{\int _{W}\lambda (x)\,\mathrm {d} x.}}$

where $\textstyle x_{i}$ is the point under consideration for acceptance or rejection.

That is, a location is uniformly randomly selected for consideration, then to determine whether to place a sample at that location a uniformly randomly drawn number in $[0,1]$ is compared to the probability density function ${\frac {\lambda (x)}{\Lambda (W)}}$ , accepting if it is smaller than the probability density function, and repeating until the previously chosen number of samples have been drawn.

## General Poisson point process

In [measure theory](https://en.wikipedia.org/wiki/Measure_theory), the Poisson point process can be further generalized to what is sometimes known as the **general Poisson point process** or **general Poisson process** by using a [Radon measure](https://en.wikipedia.org/wiki/Radon_measure) $\textstyle \Lambda$, which is a [locally finite measure](https://en.wikipedia.org/wiki/Locally_finite_measure). In general, this Radon measure $\textstyle \Lambda$ can be atomic, which means multiple points of the Poisson point process can exist in the same location of the underlying space. In this situation, the number of points at $\textstyle x$ is a Poisson random variable with mean $\textstyle \Lambda ({x})$. But sometimes the converse is assumed, so the Radon measure $\textstyle \Lambda$ is [diffuse](https://en.wikipedia.org/wiki/Diffuse) or non-atomic.

A point process $\textstyle {N}$ is a general Poisson point process with intensity $\textstyle \Lambda$ if it has the two following properties:

- the number of points in a bounded [Borel set](https://en.wikipedia.org/wiki/Borel_set) $\textstyle B$ is a Poisson random variable with mean $\textstyle \Lambda (B)$. In other words, denote the total number of points located in $\textstyle B$ by $\textstyle {N}(B)$, then the probability of random variable $\textstyle {N}(B)$ being equal to $\textstyle n$ is given by:

$\Pr\{N(B)=n\}={\frac {(\Lambda (B))^{n}}{n!}}e^{-\Lambda (B)}$

- the number of points in $\textstyle n$ disjoint Borel sets forms $\textstyle n$ independent random variables.

The Radon measure $\textstyle \Lambda$ maintains its previous interpretation of being the expected number of points of $\textstyle {N}$ located in the bounded region $\textstyle B$, namely

$\Lambda (B)=\operatorname {E} [N(B)].$

Furthermore, if $\textstyle \Lambda$ is absolutely continuous such that it has a density (which is the [Radon–Nikodym density](https://en.wikipedia.org/wiki/Radon%E2%80%93Nikodym_theorem) or derivative) with respect to the Lebesgue measure, then for all Borel sets $\textstyle B$ it can be written as:

$\Lambda (B)=\int _{B}\lambda (x)\,\mathrm {d} x,$

where the density $\textstyle \lambda (x)$ is known, among other terms, as the intensity function.

## History

### Poisson distribution

Despite its name, the Poisson point process was neither discovered nor studied by its namesake. It is cited as an example of [Stigler's law of eponymy](https://en.wikipedia.org/wiki/Stigler%27s_law_of_eponymy). The name arises from the process's inherent relation to the Poisson distribution, derived by Poisson as a limiting case of the [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution). It describes the [probability](https://en.wikipedia.org/wiki/Probability) of the sum of $\textstyle n$ [Bernoulli trials](https://en.wikipedia.org/wiki/Bernoulli_trial) with probability $\textstyle p$, often likened to the number of heads (or tails) after $\textstyle n$ biased [coin flips](https://en.wikipedia.org/wiki/Coin_flipping) with the probability of a head (or tail) occurring being $\textstyle p$. For some positive constant $\textstyle \Lambda >0$, as $\textstyle n$ increases towards infinity and $\textstyle p$ decreases towards zero such that the product $\textstyle np=\Lambda$ is fixed, the Poisson distribution more closely approximates that of the binomial.

Poisson derived the Poisson distribution, published in 1841, by examining the binomial distribution in the [limit](https://en.wikipedia.org/wiki/Limit_(mathematics) "Limit (mathematics)") of $\textstyle p$ (to zero) and $\textstyle n$ (to infinity). It only appears once in all of Poisson's work, and the result was not well known during his time. Over the following years others used the distribution without citing Poisson, including [Philipp Ludwig von Seidel](https://en.wikipedia.org/wiki/Philipp_Ludwig_von_Seidel) and [Ernst Abbe](https://en.wikipedia.org/wiki/Ernst_Abbe).  At the end of the 19th century, [Ladislaus Bortkiewicz](https://en.wikipedia.org/wiki/Ladislaus_Bortkiewicz) studied the distribution, citing Poisson, using real data on the number of deaths from horse kicks in the [Prussian army](https://en.wikipedia.org/wiki/Prussian_army).

### Discovery

There are a number of claims for early uses or discoveries of the Poisson point process. For example, [John Michell](https://en.wikipedia.org/wiki/John_Michell) in 1767, a decade before Poisson was born, was interested in the probability a star being within a certain region of another star under the erroneous assumption that the stars were "scattered by mere chance", and studied an example consisting of the six brightest [stars](https://en.wikipedia.org/wiki/Star) in the [Pleiades](https://en.wikipedia.org/wiki/Pleiades), without deriving the Poisson distribution. This work inspired [Simon Newcomb](https://en.wikipedia.org/wiki/Simon_Newcomb) to study the problem and to calculate the Poisson distribution as an approximation for the binomial distribution in 1860.

At the beginning of the 20th century the Poisson process (in one dimension) would arise independently in different situations. In Sweden 1903, [Filip Lundberg](https://en.wikipedia.org/wiki/Filip_Lundberg) published a thesis containing work, now considered fundamental and pioneering, where he proposed to model insurance claims with a homogeneous Poisson process.

In [Denmark](https://en.wikipedia.org/wiki/Denmark) [A.K. Erlang](https://en.wikipedia.org/wiki/A.K._Erlang) derived the Poisson distribution in 1909 when developing a mathematical model for the number of incoming phone calls in a finite time interval. Erlang unaware of Poisson's earlier work and assumed that the number phone calls arriving in each interval of time were independent of each other. He then found the limiting case, which is effectively recasting the Poisson distribution as a limit of the binomial distribution.

In 1910 [Ernest Rutherford](https://en.wikipedia.org/wiki/Ernest_Rutherford) and [Hans Geiger](https://en.wikipedia.org/wiki/Hans_Geiger) published experimental results on counting alpha particles. Their experimental work had mathematical contributions from [Harry Bateman](https://en.wikipedia.org/wiki/Harry_Bateman), who derived Poisson probabilities as a solution to a family of differential equations, though the solution had been derived earlier, resulting in the independent discovery of the Poisson process. After this time, there were many studies and applications of the Poisson process, but its early history is complicated, which has been explained by the various applications of the process in numerous fields by biologists, ecologists, engineers and various physical scientists.

### Early applications

The years after 1909 led to a number of studies and applications of the Poisson point process, however, its early history is complex, which has been explained by the various applications of the process in numerous fields by [biologists](https://en.wikipedia.org/wiki/Biologists), ecologists, engineers and others working in the [physical sciences](https://en.wikipedia.org/wiki/Physical_science). The early results were published in different languages and in different settings, with no standard terminology and notation used. For example, in 1922 Swedish [chemist](https://en.wikipedia.org/wiki/Chemist) and [Nobel Laureate](https://en.wikipedia.org/wiki/Nobel_Laureate) [Theodor Svedberg](https://en.wikipedia.org/wiki/Theodor_Svedberg) proposed a model in which a spatial Poisson point process is the underlying process to study how plants are distributed in plant communities. A number of mathematicians started studying the process in the early 1930s, and important contributions were made by [Andrey Kolmogorov](https://en.wikipedia.org/wiki/Andrey_Kolmogorov), [William Feller](https://en.wikipedia.org/wiki/William_Feller) and [Aleksandr Khinchin](https://en.wikipedia.org/wiki/Aleksandr_Khinchin), among others. In the field of [teletraffic engineering](https://en.wikipedia.org/wiki/Teletraffic_engineering), mathematicians and statisticians studied and used Poisson and other point processes.

### History of terms

It is believed that William Feller was the first in print to refer to it as the *Poisson process* in a 1940 paper. Although the Swede Ove Lundberg used the term *Poisson process* in his 1940 PhD dissertation, in which Feller was acknowledged as an influence, it has been claimed that Feller coined the term before 1940. It has been remarked that both Feller and Lundberg used the term as though it were well-known, implying it was already in spoken use by then. Feller worked from 1936 to 1939 alongside [Harald Cramér](https://en.wikipedia.org/wiki/Harald_Cram%C3%A9r) at [Stockholm University](https://en.wikipedia.org/wiki/Stockholm_University), where Lundberg was a PhD student under Cramér who did not use the term *Poisson process* in a book by him, finished in 1936, but did in subsequent editions, which his has led to the speculation that the term *Poisson process* was coined sometime between 1936 and 1939 at the Stockholm University.

## Terminology

The terminology of point process theory in general has been criticized for being too varied. In addition to the word *point* often being omitted, the homogeneous Poisson (point) process is also called a *stationary* Poisson (point) process, as well as *uniform* Poisson (point) process. The inhomogeneous Poisson point process, as well as being called *nonhomogeneous*, is also referred to as the *non-stationary* Poisson process.

The term *point process* has been criticized, as the term *process* can suggest over time and space, so *random point field*, resulting in the terms *Poisson random point field* or *Poisson point field* being also used. A point process is considered, and sometimes called, a random counting measure, hence the Poisson point process is also referred to as a *Poisson random measure*, a term used in the study of Lévy processes, but some choose to use the two terms for Poisson points processes defined on two different underlying spaces.

The underlying mathematical space of the Poisson point process is called a **carrier space**, or **state space**, though the latter term has a different meaning in the context of stochastic processes. In the context of point processes, the term "state space" can mean the space on which the point process is defined such as the real line, which corresponds to the index set or parameter set in stochastic process terminology.

The measure $\textstyle \Lambda$ is called the *intensity measure*, *mean measure*, or *parameter measure*, as there are no standard terms. If $\textstyle \Lambda$ has a derivative or density, denoted by $\textstyle \lambda (x)$, is called the *intensity function* of the Poisson point process. For the homogeneous Poisson point process, the derivative of the intensity measure is simply a constant $\textstyle \lambda >0$, which can be referred to as the *rate*, usually when the underlying space is the real line, or the *intensity*. It is also called the *mean rate* or the *mean density* or *rate* . For $\textstyle \lambda =1$, the corresponding process is sometimes referred to as the *standard Poisson* (point) process.

The extent of the Poisson point process is sometimes called the *exposure*.

## Notation

The notation of the Poisson point process depends on its setting and the field it is being applied in. For example, on the real line, the Poisson process, both homogeneous or inhomogeneous, is sometimes interpreted as a counting process, and the notation $\textstyle \{N(t),t\geq 0\}$ is used to represent the Poisson process.

Another reason for varying notation is due to the theory of point processes, which has a couple of mathematical interpretations. For example, a simple Poisson point process may be considered as a random set, which suggests the notation $\textstyle x\in N$, implying that $\textstyle x$ is a random point belonging to or being an element of the Poisson point process $\textstyle N$. Another, more general, interpretation is to consider a Poisson or any other point process as a random counting measure, so one can write the number of points of a Poisson point process $\textstyle {N}$ being found or located in some (Borel measurable) region $\textstyle B$ as $\textstyle N(B)$, which is a random variable. These different interpretations results in notation being used from mathematical fields such as measure theory and set theory.

For general point processes, sometimes a subscript on the point symbol, for example $\textstyle x$, is included so one writes (with set notation) $\textstyle x_{i}\in N$ instead of $\textstyle x\in N$, and $\textstyle x$ can be used for the [bound variable](https://en.wikipedia.org/wiki/Bound_variable) in integral expressions such as Campbell's theorem, instead of denoting random points. Sometimes an uppercase letter denotes the point process, while a lowercase denotes a point from the process, so, for example, the point $\textstyle x$ or $\textstyle x_{i}$ belongs to or is a point of the point process $\textstyle X$, and be written with set notation as $\textstyle x\in X$ or $\textstyle x_{i}\in X$.

Furthermore, the set theory and integral or measure theory notation can be used interchangeably. For example, for a point process $\textstyle N$ defined on the Euclidean state space $\textstyle {\mathbb {R} ^{d}}$ and a (measurable) function $\textstyle f$ on $\textstyle \mathbb {R} ^{d}$ , the expression

$\int _{\mathbb {R} ^{d}}f(x)\,\mathrm {d} N(x)=\sum \limits _{x_{i}\in N}f(x_{i}),$

demonstrates two different ways to write a summation over a point process (see also [Campbell's theorem (probability)](https://en.wikipedia.org/wiki/Campbell%27s_theorem_(probability) "Campbell's theorem (probability)")). More specifically, the integral notation on the left-hand side is interpreting the point process as a random counting measure while the sum on the right-hand side suggests a random set interpretation.

## Functionals and moment measures

In probability theory, operations are applied to random variables for different purposes. Sometimes these operations are regular expectations that produce the average or variance of a random variable. Others, such as characteristic functions (or Laplace transforms) of a random variable can be used to uniquely identify or characterize random variables and prove results like the central limit theorem. In the theory of point processes there exist analogous mathematical tools which usually exist in the forms of measures and functionals instead of moments and functions respectively.

### Laplace functionals

For a Poisson point process $\textstyle N$ with intensity measure $\textstyle \Lambda$ on some space $X$, the [Laplace functional](https://en.wikipedia.org/wiki/Laplace_functional) is given by:

$L_{N}(f)=\mathbb {E} e^{-\int _{X}f(x)\,N(\mathrm {d} x)}=e^{-\int _{X}(1-e^{-f(x)})\Lambda (\mathrm {d} x)},$

One version of [Campbell's theorem](https://en.wikipedia.org/wiki/Campbell%27s_theorem_(probability)#Second_definition:_Poisson_point_process "Campbell's theorem (probability)") involves the Laplace functional of the Poisson point process.

### Probability generating functionals

The probability generating function of non-negative integer-valued random variable leads to the probability generating functional being defined analogously with respect to any non-negative bounded function $\textstyle v$ on $\textstyle \mathbb {R} ^{d}$ such that $\textstyle 0\leq v(x)\leq 1$. For a point process $\textstyle {N}$ the probability generating functional is defined as:

$G(v)=\operatorname {E} \left[\prod _{x\in N}v(x)\right]$

where the product is performed for all the points in $N$. If the intensity measure $\textstyle \Lambda$ of $\textstyle {N}$ is locally finite, then the $G$ is well-defined for any measurable function $\textstyle u$ on $\textstyle \mathbb {R} ^{d}$. For a Poisson point process with intensity measure $\textstyle \Lambda$ the generating functional is given by:

$G(v)=e^{-\int _{\mathbb {R} ^{d}}[1-v(x)]\,\Lambda (\mathrm {d} x)},$

which in the homogeneous case reduces to

$G(v)=e^{-\lambda \int _{\mathbb {R} ^{d}}[1-v(x)]\,\mathrm {d} x}.$

### Moment measure

For a general Poisson point process with intensity measure $\textstyle \Lambda$ the first [moment measure](https://en.wikipedia.org/wiki/Moment_measure) is its intensity measure:

$M^{1}(B)=\Lambda (B),$

which for a homogeneous Poisson point process with [constant](https://en.wikipedia.org/wiki/Mathematical_constant) intensity $\textstyle \lambda$ means:

$M^{1}(B)=\lambda |B|,$

where $\textstyle |B|$ is the length, area or volume (or more generally, the [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure)) of $\textstyle B$.

### The Mecke equation

The Mecke equation characterizes the Poisson point process. Let $\mathbb {N} _{\sigma }$ be the space of all $\sigma$-finite measures on some general space ${\mathcal {Q}}$. A point process $\eta$ with intensity $\lambda$ on ${\mathcal {Q}}$ is a Poisson point process if and only if for all measurable functions $f:{\mathcal {Q}}\times \mathbb {N} _{\sigma }\to \mathbb {R} _{+}$ the following holds

$E\left[\int f(x,\eta )\eta (\mathrm {d} x)\right]=\int E\left[f(x,\eta +\delta _{x})\right]\lambda (\mathrm {d} x)$

For further details see.

### Factorial moment measure

For a general Poisson point process with intensity measure $\textstyle \Lambda$ the $\textstyle n$-th [factorial moment measure](https://en.wikipedia.org/wiki/Factorial_moment_measure) is given by the expression:

$M^{(n)}(B_{1}\times \cdots \times B_{n})=\prod _{i=1}^{n}[\Lambda (B_{i})],$

where $\textstyle \Lambda$ is the intensity measure or first moment measure of $\textstyle {N}$, which for some Borel set $\textstyle B$ is given by

$\Lambda (B)=M^{1}(B)=\operatorname {E} [N(B)].$

For a homogeneous Poisson point process the $\textstyle n$-th factorial moment measure is simply:

$M^{(n)}(B_{1}\times \cdots \times B_{n})=\lambda ^{n}\prod _{i=1}^{n}|B_{i}|,$

where $\textstyle |B_{i}|$ is the length, area, or volume (or more generally, the [Lebesgue measure](https://en.wikipedia.org/wiki/Lebesgue_measure)) of $\textstyle B_{i}$. Furthermore, the $\textstyle n$-th factorial moment density is:

$\mu ^{(n)}(x_{1},\dots ,x_{n})=\lambda ^{n}.$

## Avoidance function

The **avoidance function** or **void probability** $\textstyle v$ of a point process $\textstyle {N}$ is defined in relation to some set $\textstyle B$, which is a subset of the underlying space $\textstyle \mathbb {R} ^{d}$, as the probability of no points of $\textstyle {N}$ existing in $\textstyle B$. More precisely, for a test set $\textstyle B$, the avoidance function is given by:

$v(B)=\Pr\{N(B)=0\}.$

For a general Poisson point process $\textstyle {N}$ with intensity measure $\textstyle \Lambda$, its avoidance function is given by:

$v(B)=e^{-\Lambda (B)}$

### Rényi's theorem

Simple point processes are completely characterized by their void probabilities. In other words, complete information of a simple point process is captured entirely in its void probabilities, and two simple point processes have the same void probabilities if and if only if they are the same point processes. The case for Poisson process is sometimes known as **Rényi's theorem**, which is named after [Alfréd Rényi](https://en.wikipedia.org/wiki/Alfr%C3%A9d_R%C3%A9nyi) who discovered the result for the case of a homogeneous point process in one-dimension.

In one form, the Rényi's theorem says for a diffuse (or non-atomic) Radon measure $\textstyle \Lambda$ on $\textstyle \mathbb {R} ^{d}$ and a set $\textstyle A$ is a finite union of rectangles (so not Borel) that if $\textstyle N$ is a countable subset of $\textstyle \mathbb {R} ^{d}$ such that:

$\Pr\{N(A)=0\}=v(A)=e^{-\Lambda (A)}$

then $\textstyle {N}$ is a Poisson point process with intensity measure $\textstyle \Lambda$.

## Point process operations

Mathematical operations can be performed on point processes to get new point processes and develop new mathematical models for the locations of certain objects. One example of an operation is known as thinning which entails deleting or removing the points of some point process according to a rule, creating a new process with the remaining points (the deleted points also form a point process).

### Thinning

For the Poisson process, the independent $\textstyle p(x)$-thinning operations results in another Poisson point process. More specifically, a $\textstyle p(x)$-thinning operation applied to a Poisson point process with intensity measure $\textstyle \Lambda$ gives a point process of removed points that is also Poisson point process $\textstyle {N}_{p}$ with intensity measure $\textstyle \Lambda _{p}$, which for a bounded Borel set $\textstyle B$ is given by:

$\Lambda _{p}(B)=\int _{B}p(x)\,\Lambda (\mathrm {d} x)$

This thinning result of the Poisson point process is sometimes known as **Prekopa's theorem**. Furthermore, after randomly thinning a Poisson point process, the kept or remaining points also form a Poisson point process, which has the intensity measure

$\Lambda _{p}(B)=\int _{B}(1-p(x))\,\Lambda (\mathrm {d} x).$

The two separate Poisson point processes formed respectively from the removed and kept points are stochastically independent of each other. In other words, if a region is known to contain $\textstyle n$ kept points (from the original Poisson point process), then this will have no influence on the random number of removed points in the same region. This ability to randomly create two independent Poisson point processes from one is sometimes known as *splitting* the Poisson point process.

### Superposition

If there is a countable collection of point processes $\textstyle N_{1},N_{2},\dots$, then their superposition, or, in set theory language, their union, which is

$N=\bigcup _{i=1}^{\infty }N_{i},$

also forms a point process. In other words, any points located in any of the point processes $\textstyle N_{1},N_{2}\dots$ will also be located in the superposition of these point processes $\textstyle {N}$.

#### Superposition theorem

The **superposition theorem** of the Poisson point process says that the superposition of independent Poisson point processes $\textstyle N_{1},N_{2}\dots$ with mean measures $\textstyle \Lambda _{1},\Lambda _{2},\dots$ will also be a Poisson point process with mean measure

$\Lambda =\sum _{i=1}^{\infty }\Lambda _{i}.$

In other words, the union of two (or countably more) Poisson processes is another Poisson process. If a point $x$ is sampled from a countable $n$ union of Poisson processes, then the probability that the point $\textstyle x$ belongs to the $j$th Poisson process $N_{j}$ is given by:

$\Pr\{x\in N_{j}\}={\frac {\Lambda _{j}}{\sum _{i=1}^{n}\Lambda _{i}}}.$

For two homogeneous Poisson processes with intensities $\lambda _{1},\lambda _{2}\dots$, the two previous expressions reduce to

$\lambda =\sum _{i=1}^{\infty }\lambda _{i},$

and

$\Pr\{x\in N_{j}\}={\frac {\lambda _{j}}{\sum _{i=1}^{n}\lambda _{i}}}.$

### Clustering

The operation clustering is performed when each point $\textstyle x$ of some point process $\textstyle {N}$ is replaced by another (possibly different) point process. If the original process $\textstyle {N}$ is a Poisson point process, then the resulting process $\textstyle {N}_{c}$ is called a Poisson cluster point process.

### Random displacement

A mathematical model may require randomly moving points of a point process to other locations on the underlying mathematical space, which gives rise to a point process operation known as displacement  or translation. The Poisson point process has been used to model, for example, the movement of plants between generations, owing to the displacement theorem, which loosely says that the random independent displacement of points of a Poisson point process (on the same underlying space) forms another Poisson point process.

#### Displacement theorem

One version of the displacement theorem involves a Poisson point process $\textstyle {N}$ on $\textstyle \mathbb {R} ^{d}$ with intensity function $\textstyle \lambda (x)$. It is then assumed the points of $\textstyle {N}$ are randomly displaced somewhere else in $\textstyle \mathbb {R} ^{d}$ so that each point's displacement is independent and that the displacement of a point formerly at $\textstyle x$ is a random vector with a probability density $\textstyle \rho (x,\cdot )$. Then the new point process $\textstyle N_{D}$ is also a Poisson point process with intensity function

$\lambda _{D}(y)=\int _{\mathbb {R} ^{d}}\lambda (x)\rho (x,y)\,\mathrm {d} x.$

If the Poisson process is homogeneous with $\textstyle \lambda (x)=\lambda >0$ and if $\rho (x,y)$ is a function of $y-x$, then

$\lambda _{D}(y)=\lambda .$

In other words, after each random and independent displacement of points, the original Poisson point process still exists.

The displacement theorem can be extended such that the Poisson points are randomly displaced from one Euclidean space $\textstyle \mathbb {R} ^{d}$ to another Euclidean space $\textstyle \mathbb {R} ^{d'}$, where $\textstyle d'\geq 1$ is not necessarily equal to $\textstyle d$.

### Mapping

Another property that is considered useful is the ability to map a Poisson point process from one underlying space to another space.

#### Mapping theorem

If the mapping (or transformation) adheres to some conditions, then the resulting mapped (or transformed) collection of points also form a Poisson point process, and this result is sometimes referred to as the **mapping theorem**. The theorem involves some Poisson point process with mean measure $\textstyle \Lambda$ on some underlying space. If the locations of the points are mapped (that is, the point process is transformed) according to some function to another underlying space, then the resulting point process is also a Poisson point process but with a different mean measure $\textstyle \Lambda '$.

More specifically, one can consider a (Borel measurable) function $\textstyle f$ that maps a point process $\textstyle {N}$ with intensity measure $\textstyle \Lambda$ from one space $\textstyle S$, to another space $\textstyle T$ in such a manner so that the new point process $\textstyle {N}'$ has the intensity measure:

$\Lambda (B)'=\Lambda (f^{-1}(B))$

with no atoms, where $\textstyle B$ is a Borel set and $\textstyle f^{-1}$ denotes the inverse of the function $\textstyle f$. If $\textstyle {N}$ is a Poisson point process, then the new process $\textstyle {N}'$ is also a Poisson point process with the intensity measure $\textstyle \Lambda '$.

## Approximations with Poisson point processes

The tractability of the Poisson process means that sometimes it is convenient to approximate a non-Poisson point process with a Poisson one. The overall aim is to approximate both the number of points of some point process and the location of each point by a Poisson point process. There a number of methods that can be used to justify, informally or rigorously, approximating the occurrence of random events or phenomena with suitable Poisson point processes. The more rigorous methods involve deriving upper bounds on the probability metrics between the Poisson and non-Poisson point processes, while other methods can be justified by less formal heuristics.

### Clumping heuristic

One method for approximating random events or phenomena with Poisson processes is called the **clumping heuristic**. The general heuristic or principle involves using the Poisson point process (or Poisson distribution) to approximate events, which are considered rare or unlikely, of some stochastic process. In some cases these rare events are close to being independent, hence a Poisson point process can be used. When the events are not independent, but tend to occur in clusters or *clumps*, then if these clumps are suitably defined such that they are approximately independent of each other, then the number of clumps occurring will be close to a Poisson random variable  and the locations of the clumps will be close to a Poisson process.

### Stein's method

[Stein's method](https://en.wikipedia.org/wiki/Stein%27s_method) is a mathematical technique originally developed for approximating random variables such as [[Gaussian Distribution|Gaussian]] and Poisson variables, which has also been applied to point processes. Stein's method can be used to derive upper bounds on [probability metrics](https://en.wikipedia.org/wiki/Probability_metric), which give way to quantify how different two random mathematical objects vary stochastically. Upperbounds on probability metrics such as [total variation](https://en.wikipedia.org/wiki/Total_variation) and [Wasserstein distance](https://en.wikipedia.org/wiki/Wasserstein_distance) have been derived.

Researchers have applied Stein's method to Poisson point processes in a number of ways, such as using [Palm calculus](https://en.wikipedia.org/wiki/Palm_calculus). Techniques based on Stein's method have been developed to factor into the upper bounds the effects of certain [point process operations](https://en.wikipedia.org/wiki/Point_process_operation) such as thinning and superposition. Stein's method has also been used to derive upper bounds on metrics of Poisson and other processes such as the [Cox point process](https://en.wikipedia.org/wiki/Cox_point_process), which is a Poisson process with a random intensity measure.

## Convergence to a Poisson point process

In general, when an operation is applied to a general point process the resulting process is usually not a Poisson point process. For example, if a point process, other than a Poisson, has its points randomly and independently displaced, then the process would not necessarily be a Poisson point process. However, under certain mathematical conditions for both the original point process and the random displacement, it has been shown via limit theorems that if the points of a point process are repeatedly displaced in a random and independent manner, then the finite-distribution of the point process will converge (weakly) to that of a Poisson point process.

Similar convergence results have been developed for thinning and superposition operations that show that such repeated operations on point processes can, under certain conditions, result in the process converging to a Poisson point processes, provided a suitable rescaling of the intensity measure (otherwise values of the intensity measure of the resulting point processes would approach zero or infinity). Such convergence work is directly related to the results known as the Palm–Khinchin equations, which has its origins in the work of [Conny Palm](https://en.wikipedia.org/wiki/Conny_Palm) and [Aleksandr Khinchin](https://en.wikipedia.org/wiki/Aleksandr_Khinchin), and help explains why the Poisson process can often be used as a mathematical model of various random phenomena.

## Generalizations of Poisson point processes

The Poisson point process can be generalized by, for example, changing its intensity measure or defining on more general mathematical spaces. These generalizations can be studied mathematically as well as used to mathematically model or represent physical phenomena.

### Poisson-type random measures

The [Poisson-type random measures](https://en.wikipedia.org/wiki/Poisson-type_random_measures) (PT) are a family of three random counting measures which are closed under restriction to a subspace, i.e. closed under [Point process operation#Thinning](https://en.wikipedia.org/wiki/Point_process_operation#Thinning). These random measures are examples of the [mixed binomial process](https://en.wikipedia.org/wiki/Mixed_binomial_process) and share the distributional self-similarity property of the [Poisson random measure](https://en.wikipedia.org/wiki/Poisson_random_measure). They are the only members of the canonical non-negative [power series](https://en.wikipedia.org/wiki/Power_series) family of distributions to possess this property and include the [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution), [negative binomial distribution](https://en.wikipedia.org/wiki/Negative_binomial_distribution), and [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution). The Poisson random measure is independent on disjoint subspaces, whereas the other PT random measures (negative binomial and binomial) have positive and negative covariances. The PT random measures are discussed and include the [Poisson random measure](https://en.wikipedia.org/wiki/Poisson_random_measure), negative binomial random measure, and binomial random measure.

### Poisson point processes on more general spaces

For mathematical models the Poisson point process is often defined in Euclidean space, but has been generalized to more abstract spaces and plays a fundamental role in the study of random measures, which requires an understanding of mathematical fields such as probability theory, measure theory and topology.

In general, the concept of distance is of practical interest for applications, while topological structure is needed for Palm distributions, meaning that point processes are usually defined on mathematical spaces with metrics. Furthermore, a realization of a point process can be considered as a counting measure, so points processes are types of random measures known as random counting measures. In this context, the Poisson and other point processes have been studied on a locally compact second countable Hausdorff space.

### Cox point process

A **Cox point process**, **Cox process** or **doubly stochastic Poisson process** is a generalization of the Poisson point process by letting its intensity measure $\textstyle \Lambda$ to be also random and independent of the underlying Poisson process. The process is named after [David Cox](https://en.wikipedia.org/wiki/David_Cox_(statistician) "David Cox (statistician)") who introduced it in 1955, though other Poisson processes with random intensities had been independently introduced earlier by Lucien Le Cam and Maurice Quenouille. The intensity measure may be a realization of random variable or a random field. For example, if the [logarithm](https://en.wikipedia.org/wiki/Natural_logarithm) of the intensity measure is a [Gaussian random field](https://en.wikipedia.org/wiki/Gaussian_random_field), then the resulting process is known as a *log Gaussian Cox process*. More generally, the intensity measures is a realization of a non-negative locally finite random measure. Cox point processes exhibit a *clustering* of points, which can be shown mathematically to be larger than those of Poisson point processes. The generality and tractability of Cox processes has resulted in them being used as models in fields such as spatial statistics and wireless networks.

### Marked Poisson point process

![[media/800c3fb0616d7f3e4302132dd02aa5b9e4b87921.png]]
An illustration of a marked point process, where the unmarked point process is defined on the positive real line, which often represents time. The random marks take on values in the state space $S$ known as the <em>mark space</em>. Any such marked point process can be interpreted as an unmarked point process on the space $[0,\infty ]\times S$. The marking theorem says that if the original unmarked point process is a Poisson point process and the marks are stochastically independent, then the marked point process is also a Poisson point process on $[0,\infty ]\times S$. If the Poisson point process is homogeneous, then the gaps $\tau _{i}$ in the diagram are drawn from an exponential distribution.

For a given point process, each random point of a point process can have a random mathematical object, known as a **mark**, randomly assigned to it. These marks can be as diverse as integers, real numbers, lines, geometrical objects or other point processes. The pair consisting of a point of the point process and its corresponding mark is called a marked point, and all the marked points form a **marked point process**. It is often assumed that the random marks are independent of each other and identically distributed, yet the mark of a point can still depend on the location of its corresponding point in the underlying (state) space. If the underlying point process is a Poisson point process, then the resulting point process is a **marked Poisson point process**.

#### Marking theorem

If a general point process is defined on some [mathematical space](https://en.wikipedia.org/wiki/Mathematical_space) and the random marks are defined on another mathematical space, then the marked point process is defined on the [Cartesian product](https://en.wikipedia.org/wiki/Cartesian_product) of these two spaces. For a marked Poisson point process with independent and identically distributed marks, the **marking theorem** states that this marked point process is also a (non-marked) Poisson point process defined on the aforementioned Cartesian product of the two mathematical spaces, which is not true for general point processes.

### Compound Poisson point process

The **compound Poisson point process** or **compound Poisson process** is formed by adding random values or weights to each point of Poisson point process defined on some underlying space, so the process is constructed from a marked Poisson point process, where the marks form a collection of [independent and identically distributed](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables) non-negative random variables. In other words, for each point of the original Poisson process, there is an independent and identically distributed non-negative random variable, and then the compound Poisson process is formed from the sum of all the random variables corresponding to points of the Poisson process located in some region of the underlying mathematical space.

If there is a marked Poisson point process formed from a Poisson point process $\textstyle N$ (defined on, for example, $\textstyle \mathbb {R} ^{d}$) and a collection of independent and identically distributed non-negative marks $\textstyle \{M_{i}\}$ such that for each point $\textstyle x_{i}$ of the Poisson process $\textstyle N$ there is a non-negative random variable $\textstyle M_{i}$, the resulting compound Poisson process is then:

$C(B)=\sum _{i=1}^{N(B)}M_{i},$

where $\textstyle B\subset \mathbb {R} ^{d}$ is a Borel measurable set.

If general random variables $\textstyle \{M_{i}\}$ take values in, for example, $\textstyle d$-dimensional Euclidean space $\textstyle \mathbb {R} ^{d}$, the resulting compound Poisson process is an example of a [Lévy process](https://en.wikipedia.org/wiki/L%C3%A9vy_process) provided that it is formed from a homogeneous Point process $\textstyle N$ defined on the non-negative numbers $\textstyle [0,\infty )$.

### Failure process with the exponential smoothing of intensity functions

The failure process with the exponential smoothing of intensity functions (FP-ESI) is an extension of the nonhomogeneous Poisson process. The intensity function of an FP-ESI is an exponential smoothing function of the intensity functions at the last time points of event occurrences and outperforms other nine stochastic processes on 8 real-world failure datasets when the models are used to fit the datasets, where the model performance is measured in terms of AIC ([Akaike information criterion](https://en.wikipedia.org/wiki/Akaike_information_criterion)) and BIC ([Bayesian information criterion](https://en.wikipedia.org/wiki/Bayesian_information_criterion)).

## See also

- [Boolean model (probability theory)](https://en.wikipedia.org/wiki/Boolean_model_(probability_theory) "Boolean model (probability theory)")
- [Continuum percolation theory](https://en.wikipedia.org/wiki/Continuum_percolation_theory)
- [Compound Poisson process](https://en.wikipedia.org/wiki/Compound_Poisson_process)
- [Cox process](https://en.wikipedia.org/wiki/Cox_process)
- [Point process](https://en.wikipedia.org/wiki/Point_process)
- [Stochastic geometry](https://en.wikipedia.org/wiki/Stochastic_geometry)
- [Stochastic geometry models of wireless networks](https://en.wikipedia.org/wiki/Stochastic_geometry_models_of_wireless_networks)
- [Markovian arrival processes](https://en.wikipedia.org/wiki/Markovian_arrival_processes)

## Notes

1.  See Section 2.3.2 of Chiu, Stoyan, Kendall, Mecke or Section 1.3 of Kingman.
2.  For example, it is possible for an event *not* happening in the queueing theory sense to be an event in the probability theory sense.
3.  Instead of $\textstyle \lambda (x)$ and $\textstyle {\mathrm {d} }x$, one could write, for example, in (two-dimensional) polar coordinates $\textstyle \lambda (r,\theta )$ and $r\,dr\,d\theta$ , where $\textstyle r$ and $\textstyle \theta$ denote the radial and angular coordinates respectively, and so $\textstyle {\mathrm {d} }x$ would be an area element in this example.
4.  This set $\textstyle A$ is formed by a finite number of unions, whereas a Borel set is formed by a countable number of set operations. 
5.  Kingman calls this a probability density, but in other resources this is called a *probability kernel*.
6.  Also spelt Palm–Khintchine in, for example, *[Point Processes](https://en.wikipedia.org/wiki/Point_Processes)* by , p. 41)

## References

### Specific

1.  ^       Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
2.  ^            Stirzaker, David (2000). "Advice to Hedgehogs, or, Constants Can Vary". *The Mathematical Gazette*. **84** (500): 197–210. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/3621649](https://doi.org/10.2307%2F3621649). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0025-5572](https://search.worldcat.org/issn/0025-5572). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [3621649](https://www.jstor.org/stable/3621649). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [125163415](https://api.semanticscholar.org/CorpusID:125163415).
3.  ^            Guttorp, Peter; Thorarinsdottir, Thordis L. (2012). "What Happened to Discrete Chaos, the Quenouille Process, and the Sharp Markov Property? Some History of Stochastic Point Processes". *International Statistical Review*. **80** (2): 253–268. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1111/j.1751-5823.2012.00181.x](https://doi.org/10.1111%2Fj.1751-5823.2012.00181.x). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0306-7734](https://search.worldcat.org/issn/0306-7734). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [80836](https://api.semanticscholar.org/CorpusID:80836).
4.  G. J. Babu and E. D. Feigelson. Spatial point processes in astronomy. *Journal of statistical planning and inference*, 50(3):311–326, 1996.
5.  H. G. Othmer, S. R. Dunbar, and W. Alt. Models of dispersal in biological systems. *Journal of mathematical biology*, 26(3):263–298, 1988.
6.  ^   H. Thompson. Spatial point processes, with applications to ecology. *Biometrika*, 42(1/2):102–115, 1955.
7.  C. B. Connor and B. E. Hill. Three nonhomogeneous poisson models for the probability of basaltic volcanism: application to the yucca mountain region, nevada. *Journal of Geophysical Research: Solid Earth (1978–2012)*, 100(B6):10107–10125, 1995.
8.  Gardner, J. K.; Knopoff, L. (1974). ["Is the sequence of earthquakes in Southern California, with aftershocks removed, Poissonian?"](https://pubs.geoscienceworld.org/ssa/bssa/article-abstract/64/5/1363/117341/is-the-sequence-of-earthquakes-in-southern). *Bulletin of the Seismological Society of America*. **64** (5): 1363–1367. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1974BuSSA..64.1363G](https://ui.adsabs.harvard.edu/abs/1974BuSSA..64.1363G). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1785/BSSA0640051363](https://doi.org/10.1785%2FBSSA0640051363). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [131035597](https://api.semanticscholar.org/CorpusID:131035597).
9.  J. D. Scargle. Studies in astronomical time series analysis. v. bayesian blocks, a new method to analyze structure in photon counting data. *The Astrophysical Journal*, 504(1):405, 1998.
10. P. Aghion and P. Howitt. A Model of Growth through Creative Destruction. *Econometrica*, 60(2). 323–351, 1992.
11. M. Bertero, P. Boccacci, G. Desidera, and G. Vicidomini. Image deblurring with poisson data: from cells to galaxies. *Inverse Problems*, 25(12):123006, 2009.
12. ["The Color of Noise"](https://caseymuratori.com/blog_0010).
13. ^   F. Baccelli and B. Błaszczyszyn. *Stochastic Geometry and Wireless Networks, Volume II- Applications*, volume 4, No 1–2 of *Foundations and Trends in Networking*. NoW Publishers, 2009.
14. M. Haenggi, J. Andrews, F. Baccelli, O. Dousse, and M. Franceschetti. Stochastic geometry and random graphs for the analysis and design of wireless networks. *IEEE JSAC*, 27(7):1029–1046, September 2009.
15. ^   Leonard Kleinrock (1976). [Queueing Systems: Theory](https://archive.org/details/queueingsystems01klei). Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-49110-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-49110-1).
16. ^   A. Baddeley; I. Bárány; R. Schneider (26 October 2006). [Stochastic Geometry: Lectures given at the C.I.M.E. Summer School held in Martina Franca, Italy, September 13–18, 2004](https://books.google.com/books?id=X-m5BQAAQBAJ). Springer. p. 10. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-38175-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-38175-4).
17. ^   J. G. Andrews, R. K. Ganti, M. Haenggi, N. Jindal, and S. Weber. A primer on spatial modeling and analysis in wireless networks. *Communications Magazine, IEEE*, 48(11):156–163, 2010.
18. ^          F. Baccelli and B. Błaszczyszyn. *Stochastic Geometry and Wireless Networks, Volume I – Theory*, volume 3, No 3–4 of *Foundations and Trends in Networking*. NoW Publishers, 2009.
19. ^      Martin Haenggi (2013). [Stochastic Geometry for Wireless Networks](https://books.google.com/books?id=CLtDhblwWEgC). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-107-01469-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-107-01469-5).
20. ^          Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. pp. 51–52. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
21. ^     A. Baddeley; I. Bárány; R. Schneider (26 October 2006). [Stochastic Geometry: Lectures given at the C.I.M.E. Summer School held in Martina Franca, Italy, September 13–18, 2004](https://books.google.com/books?id=X-m5BQAAQBAJ). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-38175-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-38175-4).
22. ^    Jesper Moller; Rasmus Plenge Waagepetersen (25 September 2003). [Statistical Inference and Simulation for Spatial Point Processes](https://books.google.com/books?id=dBNOHvElXZ4C). CRC Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-203-49693-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-203-49693-0).
23. ^   R. Meester and R. Roy. Continuum percolation, volume 119 of cambridge tracts in mathematics, 1996.
24. ^    Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. pp. 41 and 51. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
25. ^     Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. pp. 41–42. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
26. , p. 22.
27. ^    .
28. , pp. 73–76.
29. ^      H. C. Tijms (18 April 2003). [A First Course in Stochastic Models](https://books.google.com/books?id=RK9yFrNxom8C). John Wiley & Sons. pp. 1–2. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-49880-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-49880-3).
30. , pp. 26–37.
31. H. C. Tijms (18 April 2003). [A First Course in Stochastic Models](https://books.google.com/books?id=RK9yFrNxom8C). John Wiley & Sons. pp. 1 and 9. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-49880-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-49880-3).
32. ^        Sheldon M. Ross (1996). [Stochastic processes](https://books.google.com/books?id=ImUPAQAAMAAJ). Wiley. pp. 59–60. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-12062-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-12062-9).
33. ^   A. Baddeley. A crash course in stochastic geometry. *Stochastic Geometry: Likelihood and Computation Eds OE Barndorff-Nielsen, WS Kendall, HNN van Lieshout (London: Chapman and Hall)*, pages 1–35, 1999.
34. D.J. Daley; David Vere-Jones (12 November 2007). [An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure](https://books.google.com/books?id=nPENXKw5kwcC). Springer Science & Business Media. pp. 1–2. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-21337-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-21337-8).
35. Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. pp. 110–111. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
36. ^      , pp. 11–12.
37. , pp. 34–39.
38. ^   Daley, Daryl J.; Vere-Jones, David (2007). *An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure*. Springer. p. 26. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0387213378](https://en.wikipedia.org/wiki/Special:BookSources/978-0387213378).
39. Jesper Moller; Rasmus Plenge Waagepetersen (25 September 2003). [Statistical Inference and Simulation for Spatial Point Processes](https://books.google.com/books?id=dBNOHvElXZ4C). CRC Press. pp. 15–16. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-203-49693-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-203-49693-0).
40. Roy L. Streit (15 September 2010). [Poisson Point Processes: Imaging, Tracking, and Sensing](https://books.google.com/books?id=KAWmFYUJ5zsC). Springer Science & Business Media. pp. 7–8. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-6923-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-6923-1).
41. ^   W. Feller. Introduction to probability theory and its applications, vol. ii pod. 1974.
42. ^     , p. 13.
43. ^    Jesper Moller; Rasmus Plenge Waagepetersen (25 September 2003). [Statistical Inference and Simulation for Spatial Point Processes](https://books.google.com/books?id=dBNOHvElXZ4C). CRC Press. p. 14. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-203-49693-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-203-49693-0).
44. , p. 20.
45. ^     H. C. Tijms (18 April 2003). [A First Course in Stochastic Models](https://books.google.com/books?id=RK9yFrNxom8C). John Wiley & Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-49880-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-49880-3).
46. Sheldon M. Ross (1996). [Stochastic processes](https://books.google.com/books?id=ImUPAQAAMAAJ). Wiley. p. 64. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-12062-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-12062-9).
47. ^        Daley, Daryl J.; Vere-Jones, David (2007). *An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure*. Springer. p. 19. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0387213378](https://en.wikipedia.org/wiki/Special:BookSources/978-0387213378).
48. , pp. 19–23.
49. , p. 42.
50. Henk C. Tijms (6 May 2003). [A First Course in Stochastic Models](https://books.google.com/books?id=eBeNngEACAAJ). Wiley. pp. 2–3. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-49881-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-49881-0).
51. Sheldon M. Ross (1996). [Stochastic processes](https://books.google.com/books?id=ImUPAQAAMAAJ). Wiley. pp. 35–36. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-12062-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-12062-9).
52. ^    , pp. 38–39.
53. , pp. 29–30.
54. Sheldon M. Ross (1996). [Stochastic processes](https://books.google.com/books?id=ImUPAQAAMAAJ). Wiley. p. 151. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-12062-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-12062-9).
55. , p. 25.
56. Daley, Daryl J.; Vere-Jones, David (2007). *An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure*. Springer. p. 29. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0387213378](https://en.wikipedia.org/wiki/Special:BookSources/978-0387213378).
57. ^    E. Merzbach and D. Nualart. A characterization of the spatial poisson process and changing time. *The Annals of Probability*, 14(4):1380–1390, 1986.
58. Feigin, Paul D. (1979). ["On the Characterization of Point Processes with the Order Statistic Property"](https://www.jstor.org/stable/3212898). *Journal of Applied Probability*. **16** (2): 297–304. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/3212898](https://doi.org/10.2307%2F3212898). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [3212898](https://www.jstor.org/stable/3212898). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [123904407](https://api.semanticscholar.org/CorpusID:123904407).
59. Sheldon M. Ross (1996). [Stochastic processes](https://books.google.com/books?id=ImUPAQAAMAAJ). Wiley. p. 235. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-12062-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-12062-9).
60. A. Papoulis and S. U. Pillai. *Probability, random variables, and stochastic processes*. Tata McGraw-Hill Education, 2002.
61. , p. 3.
62. D. Snyder and M. Miller. Random point processes in time and space 2e springer-verlag. *New York, NY*, 1991.
63. ^   Daley, Daryl J.; Vere-Jones, David (2007). *An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0387213378](https://en.wikipedia.org/wiki/Special:BookSources/978-0387213378).
64. Lawson, A. B. (1993). "A deviance residual for heterogeneous spatial poisson processes". *Biometrics*. **49** (3): 889–897. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/2532210](https://doi.org/10.2307%2F2532210). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [2532210](https://www.jstor.org/stable/2532210).
65. ^   Daley, Daryl J.; Vere-Jones, David (2007). *An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure*. Springer. pp. 19–23. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0387213378](https://en.wikipedia.org/wiki/Special:BookSources/978-0387213378).
66. Lee, C.-H.; Shih, C.-Y.; Chen, Y.-S. (2012). "Stochastic geometry based models for modeling cellular networks in urban areas". *Wireless Networks*. **19** (6): 1063–1072. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s11276-012-0518-0](https://doi.org/10.1007%2Fs11276-012-0518-0). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [8409538](https://api.semanticscholar.org/CorpusID:8409538).
67. ^    D.J. Daley; David Vere-Jones (12 November 2007). [An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure](https://books.google.com/books?id=nPENXKw5kwcC). Springer Science & Business Media. p. 31. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-21337-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-21337-8).
68. Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. pp. 38–40 and 53–54. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
69. ^   D.J. Daley; David Vere-Jones (12 November 2007). [An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure](https://books.google.com/books?id=nPENXKw5kwcC). Springer Science & Business Media. p. 25. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-21337-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-21337-8).
70. , p. X.
71. Roy L. Streit (15 September 2010). [Poisson Point Processes: Imaging, Tracking, and Sensing](https://books.google.com/books?id=KAWmFYUJ5zsC). Springer Science & Business Media. p. 6. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-6923-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-6923-1).
72. ^    H. C. Tijms (18 April 2003). [A First Course in Stochastic Models](https://books.google.com/books?id=RK9yFrNxom8C). John Wiley & Sons. pp. 22–23. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-49880-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-49880-3).
73. L. Citi; D. Ba; E.N. Brown & R. Barbieri (2014). ["Likelihood methods for point processes with refractoriness"](https://dspace.mit.edu/bitstream/1721.1/85015/2/Citi-2013-Likelihood%20Methods%20f.pdf) (PDF). *Neural Computation*. **26** (2): 237–263. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/NECO_a_00548](https://doi.org/10.1162%2FNECO_a_00548). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[1721.1/85015](https://hdl.handle.net/1721.1%2F85015). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [24206384](https://pubmed.ncbi.nlm.nih.gov/24206384). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [1436173](https://api.semanticscholar.org/CorpusID:1436173).
74. ^   A. Baddeley; I. Bárány; R. Schneider (26 October 2006). [Stochastic Geometry: Lectures given at the C.I.M.E. Summer School held in Martina Franca, Italy, September 13–18, 2004](https://books.google.com/books?id=X-m5BQAAQBAJ). Springer. p. 12. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-38175-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-38175-4).
75. Sheldon M. Ross (1996). [Stochastic processes](https://books.google.com/books?id=ImUPAQAAMAAJ). Wiley. pp. 78–81. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-12062-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-12062-9).
76. A. Heuer, C. Mueller, and O. Rubner. Soccer: Is scoring goals a predictable Poissonian process? *EPL*, 89(3):38007, 2010.
77. J. Y. Hwang, W. Kuo, and C. Ha. Modeling of integrated circuit yield using a spatial nonhomogeneous poisson process. *Semiconductor Manufacturing, IEEE Transactions on*, 24(3):377–384, 2011.
78. M. Krko{\vs}ek, M. A. Lewis, and J. P. Volpe. Transmission dynamics of parasitic sea lice from farm to wild salmon. *Proceedings of the Royal Society B: Biological Sciences*, 272(1564):689–696, 2005.
79. P. A. Lewis and G. S. Shedler. Simulation of nonhomogeneous Poisson processes by thinning. *Naval Research Logistics Quarterly*, 26(3):403–413, 1979.
80. , pp. 10.
81. , pp. 3–6.
82. Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. p. 44. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
83. Martin Haenggi (2013). [Stochastic Geometry for Wireless Networks](https://books.google.com/books?id=CLtDhblwWEgC). Cambridge University Press. p. 11. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-107-01469-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-107-01469-5).
84. ^     Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. pp. 53–55. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
85. Roy L. Streit (15 September 2010). [Poisson Point Processes: Imaging, Tracking, and Sensing](https://books.google.com/books?id=KAWmFYUJ5zsC). Springer Science & Business Media. pp. 13–14. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-6923-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-6923-1).
86. Roy L. Streit (15 September 2010). [Poisson Point Processes: Imaging, Tracking, and Sensing](https://books.google.com/books?id=KAWmFYUJ5zsC). Springer Science & Business Media. pp. 14–16. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-6923-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-6923-1).
87. ^   Martin Haenggi (2013). [Stochastic Geometry for Wireless Networks](https://books.google.com/books?id=CLtDhblwWEgC&pg=PA18). Cambridge University Press. pp. 18–19. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-107-01469-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-107-01469-5).
88. ^   Good, I. J. (1986). ["Some Statistical Applications of Poisson's Work"](https://doi.org/10.1214%2Fss%2F1177013690). *Statistical Science*. **1** (2): 157–170. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/ss/1177013690](https://doi.org/10.1214%2Fss%2F1177013690). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0883-4237](https://search.worldcat.org/issn/0883-4237).
89. ^    Grimmett, G.; Stirzaker, D. (2001). *Probability and Random Processes* (3rd ed.). Oxford University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-19-857222-0](https://en.wikipedia.org/wiki/Special:BookSources/0-19-857222-0).
90. Stigler, S. M. (1982). "Poisson on the Poisson Distribution". *Statistics & Probability Letters*. **1** (1): 33–35. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0167-7152(82)90010-4](https://doi.org/10.1016%2F0167-7152%2882%2990010-4).
91. , pp. 8–9.
92. Quine, M.; [Seneta, E.](https://en.wikipedia.org/wiki/Eugene_Seneta) (1987). "Bortkiewicz's data and the law of small numbers". *International Statistical Review*. **55** (2): 173–181. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2307/1403193](https://doi.org/10.2307%2F1403193). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [1403193](https://www.jstor.org/stable/1403193).
93. Embrechts, Paul; Frey, Rüdiger; Furrer, Hansjörg (2001). "Stochastic processes in insurance and finance". *Stochastic Processes: Theory and Methods*. Handbook of Statistics. Vol. 19. p. 367. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/S0169-7161(01)19014-0](https://doi.org/10.1016%2FS0169-7161%2801%2919014-0). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780444500144](https://en.wikipedia.org/wiki/Special:BookSources/9780444500144). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0169-7161](https://search.worldcat.org/issn/0169-7161).
94. Cramér, Harald (1969). "Historical review of Filip Lundberg's works on risk theory". *Scandinavian Actuarial Journal*. **1969** (sup3): 6–12. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/03461238.1969.10404602](https://doi.org/10.1080%2F03461238.1969.10404602). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0346-1238](https://search.worldcat.org/issn/0346-1238).
95. Illian, J.; Penttinen, A.; Stoyan, H.; Stoyan, D. (2008). *Statistical analysis and modelling of spatial point patterns*. Vol. 70. John Wiley & Sons. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-470-01491-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-470-01491-2).
96. Kingman, J. (2009). "The first Erlang century—and the next". *Queueing Systems*. **63** (1–4): 3–12. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s11134-009-9147-4](https://doi.org/10.1007%2Fs11134-009-9147-4). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [38588726](https://api.semanticscholar.org/CorpusID:38588726).
97. ^   Haugen, R. B. (1995). "The life and work of Conny Palm. some personal comments and experiences". *VTT Symposium*. **154**. Valtion teknillinen tutkimuskeskus: 207. [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0357-9387](https://search.worldcat.org/issn/0357-9387).
98. ^   D.J. Daley; David Vere-Jones (12 November 2007). [An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure](https://books.google.com/books?id=nPENXKw5kwcC). Springer Science & Business Media. pp. 13–14. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-21337-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-21337-8).
99. J. Grandell. *Mixed poisson processes*, volume 77. CRC Press, 1997.
100. , p. X.
101. Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. p. 109. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
102. G. Mikhailov and T. Averina. Statistical modeling of inhomogeneous random functions on the basis of poisson point fields. In *Doklady Mathematics*, volume 82, pages 701–704. Springer, 2010.
103. I. Molchanov. *Theory of random sets*. Springer Science \\ Business Media, 2006.
104. ^   K. Sato. Lévy processes and infinite divisibility, 1999.
105. V. Mandrekar and B. Rüdiger. *Stochastic Integration in Banach Spaces*. Springer, 2015.
106. D. Applebaum. *Lévy processes and stochastic calculus*. Cambridge university press, 2009.
107. E. F. Harding and R. Davidson. *Stochastic geometry: a tribute to the memory of Rollo Davidson*. Wiley, 1974.
108. ^   L. H. Chen and A. Xia. Stein's method, Palm theory and Poisson process approximation. *Annals of probability*, pages 2545–2569, 2004.
109. , p. 8.
110. ^   Jesper Moller; Rasmus Plenge Waagepetersen (25 September 2003). [Statistical Inference and Simulation for Spatial Point Processes](https://books.google.com/books?id=dBNOHvElXZ4C). CRC Press. p. 7. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-203-49693-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-203-49693-0).
111. Emanuel Parzen (17 June 2015). [Stochastic Processes](https://books.google.com/books?id=0mB2CQAAQBAJ). Courier Dover Publications. pp. 7–8 and 29–30. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-79688-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-79688-8).
112. John Lamperti (1977). [Stochastic processes: a survey of the mathematical theory](https://books.google.com/books?id=Pd4cvgAACAAJ). Springer-Verlag. pp. 1 and 10–11. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-90275-1](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-90275-1).
113. Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. p. 112. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
114. Daley, Daryl J.; Vere-Jones, David (2007). *An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure*. Springer. p. 20. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0387213378](https://en.wikipedia.org/wiki/Special:BookSources/978-0387213378).
115. ^   J. Grandell. Point processes and random measures. *Advances in Applied Probability*, pages 502–526, 1977.
116. [Some Poisson models](http://www.vosesoftware.com/ModelRiskHelp/index.htm#Probability_theory_and_statistics/Stochastic_processes/Some_Poisson_models.htm), Vose Software, retrieved 18 January 2016
117. Helske, Jouni (25 June 2015), ["KFAS: Exponential Family State Space Models in R"](https://cran.r-project.org/web/packages/KFAS/vignettes/KFAS.pdf) (PDF), *Journal of Statistical Software*, **78** (10), [Comprehensive R Archive Network](https://en.wikipedia.org/wiki/R_(programming_language)#CRAN "R (programming language)"), [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1612.01907](https://arxiv.org/abs/1612.01907), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.18637/jss.v078.i10](https://doi.org/10.18637%2Fjss.v078.i10), [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [14379617](https://api.semanticscholar.org/CorpusID:14379617), retrieved 18 January 2016
118. ^    Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. p. 100. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
119. A. Karr. *Probability*. Springer Texts in Statistics Series. Springer-Verlag, 1993.
120. Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. pp. 120–126. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
121. D.J. Daley; David Vere-Jones (12 November 2007). [An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure](https://books.google.com/books?id=nPENXKw5kwcC). Springer Science & Business Media. pp. 52–75. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-21337-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-21337-8).
122. Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. pp. 125–126. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
123. Günter Last; Mathew Penrose (8 August 2017). lastpenrose2017.pdf (PDF).
124. ^   Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. pp. 47–48. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
125. Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. p. 42. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
126. Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. p. 43. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
127. ^   , pp. 34.
128. D.J. Daley; David Vere-Jones (12 November 2007). [An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure](https://books.google.com/books?id=nPENXKw5kwcC). Springer Science & Business Media. pp. 384–385. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-21337-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-21337-8).
129. ^   Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. p. 158. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
130. Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. p. 160. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
131. [D. Bertsekas](https://en.wikipedia.org/wiki/Dimitri_Bertsekas) and [J. Tsitsiklis](https://en.wikipedia.org/wiki/John_Tsitsiklis). Introduction to probability, ser. *Athena Scientific optimization and computation series. Athena Scientific*, 2008.
132. J. F. Hayes. *Modeling and analysis of computer communications networks*. Perseus Publishing, 1984.
133. Sung Nok Chiu; Dietrich Stoyan; Wilfrid S. Kendall; Joseph Mecke (27 June 2013). [Stochastic Geometry and Its Applications](https://books.google.com/books?id=825NfM6Nc-EC). John Wiley & Sons. p. 165. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-118-65825-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-118-65825-3).
134. , p. 16.
135. ^     , p. 61.
136. D.J. Daley; David Vere-Jones (12 November 2007). [An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure](https://books.google.com/books?id=nPENXKw5kwcC). Springer Science & Business Media. pp. 166–167. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-21337-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-21337-8).
137. ^   , pp. 18.
138. Geoffrey Grimmett; David Stirzaker (31 May 2001). [Probability and Random Processes](https://books.google.com/books?id=G3ig-0M4wSIC). OUP Oxford. p. 284. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-19-857222-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-19-857222-0).
139. ^      L. H. Chen, A. Röllin, et al. Approximating dependent rare events. *Bernoulli*, 19(4):1243–1267, 2013.
140. ^   R. Arratia, S. Tavare, et al. {Review: D. Aldous, Probability Approximations via the Poisson Clumping Heuristic; AD Barbour, L. Holst, S. Janson, Poisson Approximation}. *The Annals of Probability*, 21(4):2269–2279, 1993.
141. ^   D. Aldous. *Poisson Clumping Heuristic*. Wiley Online Library, 1989.
142. A. D. Barbour and T. C. Brown. Stein's method and point process approximation. *Stochastic Processes and their Applications*, 43(1):9–31, 1992.
143. D. Schuhmacher. Distance estimates for dependent superpositions of point processes. *Stochastic processes and their applications*, 115(11):1819–1837, 2005.
144. D. Schuhmacher. Distance estimates for poisson process approximations of dependent thinnings. *Electronic Journal of Probability*, 10:165–201, 2005.
145. ^    D.J. Daley; David Vere-Jones (12 November 2007). [An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure](https://books.google.com/books?id=nPENXKw5kwcC). Springer Science & Business Media. pp. 131–132. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-21337-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-21337-8).
146. D.J. Daley; David Vere-Jones (12 November 2007). [An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure](https://books.google.com/books?id=nPENXKw5kwcC). Springer Science & Business Media. p. 146. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-21337-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-21337-8).
147. Caleb Bastian, Gregory Rempala. Throwing stones and collecting bones: Looking for Poisson-like random measures, Mathematical Methods in the Applied Sciences, 2020. [doi:10.1002/mma.6224](https://doi.org/10.1002/mma.6224)
148. Olav Kallenberg (1983). [Random measures](https://books.google.com/books?id=bBnvAAAAMAAJ). Akademie-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-12-394960-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-12-394960-8).
149. , pp. 79–84.
150. D.J. Daley; David Vere-Jones (12 November 2007). [An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure](https://books.google.com/books?id=nPENXKw5kwcC). Springer Science & Business Media. pp. 368–413. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-21337-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-21337-8).
151. A. E. Gelfand, P. Diggle, P. Guttorp, and M. Fuentes. *Handbook of spatial statistics*, Chapter 9. CRC press, 2010.
152. O. Kallenberg. *Random measures*. Academic Pr, 1983.
153. J. Møller, A. R. Syversveen, and R. P. Waagepetersen. Log Gaussian Cox Processes. *Scandinavian journal of statistics*, 25(3):451–482, 1998.
154. J. Møller and R. P. Waagepetersen. Modern statistics for spatial point processes. *Scandinavian Journal of Statistics*, 34(4):643–684, 2007.
155. Jesper Moller; Rasmus Plenge Waagepetersen (25 September 2003). [Statistical Inference and Simulation for Spatial Point Processes](https://books.google.com/books?id=dBNOHvElXZ4C). CRC Press. p. 8. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-203-49693-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-203-49693-0).
156. Martin Haenggi (2013). [Stochastic Geometry for Wireless Networks](https://books.google.com/books?id=CLtDhblwWEgC). Cambridge University Press. pp. 138–140. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-107-01469-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-107-01469-5).
157. A. Baddeley; I. Bárány; R. Schneider (26 October 2006). [Stochastic Geometry: Lectures given at the C.I.M.E. Summer School held in Martina Franca, Italy, September 13–18, 2004](https://books.google.com/books?id=X-m5BQAAQBAJ). Springer. pp. 19–21. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-38175-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-38175-4).
158. ^   , p. 55.
159. François Baccelli; Bartlomiej Blaszczyszyn (2009). [Stochastic Geometry and Wireless Networks](https://books.google.com/books?id=H3ZkTN2pYS4C). Now Publishers Inc. pp. 291–293. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-60198-264-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-60198-264-3).
160. Roy L. Streit (15 September 2010). [Poisson Point Processes: Imaging, Tracking, and Sensing](https://books.google.com/books?id=KAWmFYUJ5zsC). Springer Science & Business Media. pp. 205–206. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4419-6923-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4419-6923-1).
161. , pp. 198–199.
162. Daley, Daryl J.; Vere-Jones, David (2007). *An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure*. Springer. p. 198. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0387213378](https://en.wikipedia.org/wiki/Special:BookSources/978-0387213378).
163. David Applebaum (5 July 2004). [Lévy Processes and Stochastic Calculus](https://books.google.com/books?id=q7eDUjdJxIkC). Cambridge University Press. pp. 46–47. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-83263-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-83263-2).
164. Wu, S. (2019). [A failure process model with the exponential smoothing of intensity functions](https://doi.org/10.1016/j.ejor.2018.11.045). *European Journal of Operational Research*, 275(2), 502–513

### General

#### Books

- A. Baddeley; I. Bárány; R. Schneider (26 October 2006). [Stochastic Geometry: Lectures given at the C.I.M.E. Summer School held in Martina Franca, Italy, September 13–18, 2004](https://books.google.com/books?id=X-m5BQAAQBAJ). Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-38175-4](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-38175-4).
- [Cox, D. R.](https://en.wikipedia.org/wiki/David_Cox_(statistician) "David Cox (statistician)"); [Isham, Valerie](https://en.wikipedia.org/wiki/Valerie_Isham) (1980). [*Point Processes*](https://en.wikipedia.org/wiki/Point_Processes). Chapman & Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-412-21910-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-412-21910-8).
- Daley, Daryl J.; Vere-Jones, David (2003). *An Introduction to the Theory of Point Processes: Volume I: Elementary Theory and Methods*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1475781090](https://en.wikipedia.org/wiki/Special:BookSources/978-1475781090).
- Daley, Daryl J.; Vere-Jones, David (2007). *An Introduction to the Theory of Point Processes: Volume II: General Theory and Structure*. Springer. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0387213378](https://en.wikipedia.org/wiki/Special:BookSources/978-0387213378).
- [Kingman, John Frank](https://en.wikipedia.org/wiki/John_Kingman) (1992). *Poisson processes*. Clarendon Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0198536932](https://en.wikipedia.org/wiki/Special:BookSources/978-0198536932).
- Moller, Jesper; Waagepetersen, Rasmus P. (2003). *Statistical Inference and Simulation for Spatial Point Processes*. CRC Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1584882657](https://en.wikipedia.org/wiki/Special:BookSources/978-1584882657).
- Ross, S. M. (1996). *Stochastic Processes*. Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-12062-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-12062-9).
- Snyder, D. L.; Miller, M. I. (1991). *Random Point Processes in Time and Space*. Springer-Verlag. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-387-97577-1](https://en.wikipedia.org/wiki/Special:BookSources/978-0-387-97577-1).
- Stoyan, Dietrich; Kendall, Wilfred S.; Mecke, Joseph (1995). *Stochastic geometry and its applications*. Wiley. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0471950998](https://en.wikipedia.org/wiki/Special:BookSources/978-0471950998).
- Streit, Streit (2010). *Poisson Point Processes: Imaging, Tracking, and Sensing*. Springer Science& Business Media. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1441969224](https://en.wikipedia.org/wiki/Special:BookSources/978-1441969224).
- H. C. Tijms (18 April 2003). [A First Course in Stochastic Models](https://books.google.com/books?id=RK9yFrNxom8C). John Wiley & Sons. pp. 22–23. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-49880-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-49880-3).

#### Articles

- Stirzaker, David (2000). "Advice to hedgehogs, or, constants can vary". *The Mathematical Gazette*.
- Guttorp, Peter; Thorarinsdottir, Thordis L. (2012). "What happened to discrete chaos, the Quenouille process, and the sharp Markov property? Some history of stochastic point processes". *International Statistical Review*.
