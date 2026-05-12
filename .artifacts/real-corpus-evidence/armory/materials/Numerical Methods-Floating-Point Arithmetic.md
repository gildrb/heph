[[numerical-methods.base]]

> Source: [[Floating-Point Arithmetic]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/d1f0f3a860c940c249cf14a668446f66ea06e4d3.jpg]]
An early electromechanical programmable computer, the [Z3](https://en.wikipedia.org/wiki/Z3_(computer)), included floating-point arithmetic (replica on display at [Deutsches Museum](https://en.wikipedia.org/wiki/Deutsches_Museum) in [Munich](https://en.wikipedia.org/wiki/Munich)).

In [computing](https://en.wikipedia.org/wiki/Computing), **floating-point arithmetic** (**FP**) is [arithmetic](https://en.wikipedia.org/wiki/Arithmetic) on subsets of [real numbers](https://en.wikipedia.org/wiki/Real_number) formed by a *[significand](https://en.wikipedia.org/wiki/Significand)* (a [signed](https://en.wikipedia.org/wiki/Sign_(mathematics) "Sign (mathematics)") sequence of a fixed number of digits in some [base](https://en.wikipedia.org/wiki/Radix)) multiplied by an [integer power](https://en.wikipedia.org/wiki/Integer_power) of that base. Numbers of this form are called **floating-point numbers**.

For example, the number 2469/200 is a floating-point number in base ten with five digits: 

$$
2469/200=12.345=\!\underbrace {12345} _{\text{significand}}\!\times \!\underbrace {10} _{\text{base}}\!\!\!\!\!\!\!\overbrace {{}^{-3}} ^{\text{exponent}}
$$

 However, 7716/625 = 12.3456 is not a floating-point number in base ten with five digits—it needs six digits. The nearest floating-point number with only five digits is 12.346. And 1/3 = 0.3333… is not a floating-point number in base ten with any finite number of digits. In practice, most floating-point systems use [base two](https://en.wikipedia.org/wiki/Binary_number), though base ten ([decimal floating point](https://en.wikipedia.org/wiki/Decimal_floating_point)) is also common.

Floating-point arithmetic operations, such as addition and division, approximate the corresponding real number arithmetic operations by [rounding](https://en.wikipedia.org/wiki/Rounding) any result that is not a floating-point number itself to a nearby floating-point number. For example, in a floating-point arithmetic with five base-ten digits, the sum 12.345 + 1.0001 = 13.3451 might be rounded to 13.345.

The term *floating point* refers to the fact that the number's [radix point](https://en.wikipedia.org/wiki/Radix_point) can "float" anywhere to the left, right, or between the [significant digits](https://en.wikipedia.org/wiki/Significant_digits) of the number. This position is indicated by the exponent, so floating point can be considered a form of [scientific notation](https://en.wikipedia.org/wiki/Scientific_notation).

A floating-point system can be used to represent, with a fixed number of digits, numbers of very different [orders of magnitude](https://en.wikipedia.org/wiki/Orders_of_magnitude_(numbers) "Orders of magnitude (numbers)") — such as the number of meters [between galaxies](https://en.wikipedia.org/wiki/Orders_of_magnitude_(length)#100_zettametres "Orders of magnitude (length)") or [between protons in an atom](https://en.wikipedia.org/wiki/Orders_of_magnitude_(length)#10_femtometres "Orders of magnitude (length)"). For this reason, floating-point arithmetic is often used to allow very small and very large real numbers that require fast processing times. The result of this [dynamic range](https://en.wikipedia.org/wiki/Dynamic_range) is that the numbers that can be represented are not uniformly spaced; the difference between two consecutive representable numbers varies with their exponent.

![[media/77b6b46a791995e79cf7fd249c0201fa8797bf50.png]]
Single-precision floating-point numbers on a [number line](https://en.wikipedia.org/wiki/Number_line): the green lines mark representable values.

![[media/b410815daeaaca61d18749702111f7c50b4ab382.png]]
Augmented version above showing both [signs](https://en.wikipedia.org/wiki/Signed_number_representations) of representable values

Over the years, a variety of floating-point representations have been used in computers. In 1985, the [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754) Standard for Floating-Point Arithmetic was established, and since the 1990s, the most commonly encountered representations are those defined by the IEEE.

The speed of floating-point operations, commonly measured in terms of [FLOPS](https://en.wikipedia.org/wiki/FLOPS), is an important characteristic of a [computer system](https://en.wikipedia.org/wiki/Computer_system), especially for applications that involve intensive mathematical calculations.

Floating-point numbers can be computed using software implementations (softfloat) or hardware implementations (hardfloat). [Floating-point units](https://en.wikipedia.org/wiki/Floating-point_unit) (FPUs, colloquially math [coprocessors](https://en.wikipedia.org/wiki/Coprocessor)) are specially designed to carry out operations on floating-point numbers and are part of most computer systems. When FPUs are not available, software implementations can be used instead.

## Overview

### Floating-point numbers

A [number representation](https://en.wikipedia.org/wiki/Number_representation) specifies some way of encoding a number, usually as a string of digits.

There are several mechanisms by which strings of digits can represent numbers. In standard mathematical notation, the digit string can be of any length, and the location of the [radix point](https://en.wikipedia.org/wiki/Radix_point) is indicated by placing an explicit ["point" character](https://en.wikipedia.org/wiki/Decimal_separator) (dot or comma) there. If the radix point is not specified, then the string implicitly represents an [integer](https://en.wikipedia.org/wiki/Integer) and the unstated radix point would be off the right-hand end of the string, next to the least significant digit. In [fixed-point](https://en.wikipedia.org/wiki/Fixed-point_arithmetic) systems, a position in the string is specified for the radix point. So a fixed-point scheme might use a string of 8 decimal digits with the decimal point in the middle, whereby "00012345" would represent 0001.2345.

In [scientific notation](https://en.wikipedia.org/wiki/Scientific_notation), the given number is scaled by a [power of 10](https://en.wikipedia.org/wiki/Power_of_10), so that it lies within a specific range—typically between 1 and 10, with the radix point appearing immediately after the first digit. As a power of ten, the scaling factor is then indicated separately at the end of the number. For example, the orbital period of [Jupiter](https://en.wikipedia.org/wiki/Jupiter)'s moon [Io](https://en.wikipedia.org/wiki/Io_(moon) "Io (moon)") is 152,853.5047 seconds, a value that would be represented in standard-form scientific notation as 1.528535047×10<sup>5</sup> seconds.

Floating-point representation is similar in concept to scientific notation. Logically, a floating-point number consists of:

- A signed (meaning positive or negative) digit string of a given length in a given [radix](https://en.wikipedia.org/wiki/Radix) (or base). This digit string is referred to as the *[significand](https://en.wikipedia.org/wiki/Significand)*, *mantissa*, or *coefficient*. The length of the significand determines the *precision* to which numbers can be represented. The radix point position is assumed always to be somewhere within the significand—often just after or just before the most significant digit, or to the right of the rightmost (least significant) digit. This article generally follows the convention that the radix point is set just after the most significant (leftmost) digit.
- A signed integer [exponent](https://en.wikipedia.org/wiki/Exponent) (also referred to as the *characteristic*, or *scale*), which modifies the magnitude of the number.

To derive the value of the floating-point number, the *significand* is multiplied by the *base* raised to the power of the *exponent*, equivalent to shifting the radix point from its implied position by a number of places equal to the value of the exponent—to the right if the exponent is positive or to the left if the exponent is negative.

Using base-10 (the familiar [decimal](https://en.wikipedia.org/wiki/Decimal_representation) notation) as an example, the number 152,853.5047, which has ten decimal digits of precision, is represented as the significand 1528535047 together with 5 as the exponent. To determine the actual value, a decimal point is placed after the first digit of the significand and the result is multiplied by 10<sup>5</sup> to give 1.528535047×10<sup>5</sup>, or 152,853.5047. In storing such a number, the base (10) need not be stored, since it will be the same for the entire range of supported numbers, and can thus be inferred.

Symbolically, this final value is: 

$$
{\frac {s}{b^{\,p-1}}}\times b^{e},
$$

where s is the significand (ignoring any implied decimal point), p is the precision (the number of digits in the significand), b is the base (in our example, this is the number *ten*), and e is the exponent.

Historically, several number bases have been used for representing floating-point numbers, with base two ([binary](https://en.wikipedia.org/wiki/Binary_numeral_system)) being the most common, followed by base ten ([decimal floating point](https://en.wikipedia.org/wiki/Decimal_floating_point)), and other less common varieties, such as base sixteen ([hexadecimal floating point](https://en.wikipedia.org/wiki/Hexadecimal_floating_point)), base eight (octal floating point), base four (quaternary floating point), base three ([balanced ternary floating point](https://en.wikipedia.org/wiki/Balanced_ternary_floating_point)) and even base 256 and base 65,536.

A floating-point number is a [rational number](https://en.wikipedia.org/wiki/Rational_number), because it can be represented as one integer divided by another; for example 1.45×10<sup>3</sup> is (145/100)×1000 or 145,000/100. The base determines the fractions that can be represented; for instance, 1/5 cannot be represented exactly as a floating-point number using a binary base, but 1/5 can be represented exactly using a decimal base (0.2, or 2×10<sup>−1</sup>). However, 1/3 cannot be represented exactly by either binary (0.010101...) or decimal (0.333...), but in [base 3](https://en.wikipedia.org/wiki/Ternary_numeral_system), it is trivial (0.1 or 1×3<sup>−1</sup>) . The occasions on which infinite expansions occur [depend on the base and its prime factors](https://en.wikipedia.org/wiki/Positional_notation#Infinite_representations).

The way in which the significand (including its sign) and exponent are stored in a computer is implementation-dependent. The common IEEE formats are described in detail later and elsewhere, but as an example, in the binary single-precision (32-bit) floating-point representation, $p=24$, and so the significand is a string of 24 [bits](https://en.wikipedia.org/wiki/Bit). For instance, the number [π](https://en.wikipedia.org/wiki/Pi)'s first 33 bits are: 

$$
11001001\ 00001111\ 1101101{\underline {0}}\ 10100010\ 0.
$$

In this binary expansion, let us denote the positions from 0 (leftmost bit, or most significant bit) to 32 (rightmost bit). The 24-bit significand will stop at position 23, shown as the underlined bit 0 above. The next bit, at position 24, is called the *round bit* or *rounding bit*. It is used to round the 33-bit approximation to the nearest 24-bit number (there are [specific rules for halfway values](https://en.wikipedia.org/wiki/Rounding#Tie-breaking), which is not the case here). This bit, which is 1 in this example, is added to the integer formed by the leftmost 24 bits, yielding: 

$$
11001001\ 00001111\ 1101101{\underline {1}}.
$$

When this is stored in memory using the IEEE 754 encoding, this becomes the [significand](https://en.wikipedia.org/wiki/Significand) s. The significand is assumed to have a binary point to the right of the leftmost bit. So, the binary representation of π is calculated from left-to-right as follows: 

$$
{\begin{aligned}&{\biggl (}\sum _{n=0}^{p-1}{\text{bit}}_{n}\times 2^{-n}{\biggr )}\times 2^{e}\\&\qquad {}=\left(1\times 2^{-0}+1\times 2^{-1}+0\times 2^{-2}+0\times 2^{-3}+\cdots +1\times 2^{-23}\right)\times 2^{1}\\[2mu]&\qquad {}\approx 1.57079637\times 2\\[3mu]&\qquad {}\approx 3.1415927\end{aligned}}
$$

where p is the precision (24 in this example), n is the position of the bit of the significand from the left (starting at 0 and finishing at 23 here) and e is the exponent (1 in this example).

It can be required that the most significant digit of the significand of a non-zero number be non-zero (except when the corresponding exponent would be smaller than the minimum one). This process is called *normalization*. For binary formats (which uses only the digits 0 and 1), this non-zero digit is necessarily 1. Therefore, it does not need to be represented in memory, allowing the format to have one more bit of precision. This rule is variously called the *leading bit convention*, the *implicit bit convention*, the *hidden bit convention*, or the *assumed bit convention*.

### Alternatives to floating-point numbers

The floating-point representation is by far the most common way of representing in computers an approximation to real numbers. However, there are alternatives:

- [Fixed-point](https://en.wikipedia.org/wiki/Fixed-point_arithmetic) representation uses integer hardware operations controlled by a software implementation of a specific convention about the location of the binary or decimal point, for example, 6 bits or digits from the right. The hardware to manipulate these representations is less costly than floating point, and it can be used to perform normal integer operations, too. Binary fixed point is usually used in special-purpose applications on embedded processors that can only do integer arithmetic, but decimal fixed point is common in commercial applications.
- [Logarithmic number systems](https://en.wikipedia.org/wiki/Logarithmic_number_system) (LNSs) represent a real number by the logarithm of its absolute value and a sign bit. The value distribution is similar to floating point, but the value-to-representation curve (*i.e.*, the graph of the logarithm function) is smooth (except at 0). Conversely to floating-point arithmetic, in a logarithmic number system multiplication, division and exponentiation are simple to implement, but addition and subtraction are complex. The ([symmetric](https://en.wikipedia.org/wiki/Symmetric_level-index_arithmetic)) [level-index arithmetic](https://en.wikipedia.org/wiki/Level-index_arithmetic) (LI and SLI) of Charles Clenshaw, [Frank Olver](https://en.wikipedia.org/wiki/Frank_William_John_Olver) and Peter Turner is a scheme based on a [generalized logarithm](https://en.wikipedia.org/wiki/Generalized_logarithm) representation.
- [Tapered floating-point representation](https://en.wikipedia.org/wiki/Tapered_floating-point_representation), used in [Unum](https://en.wikipedia.org/wiki/Unum_(number_format) "Unum (number format)") formats, including [Posit](https://en.wikipedia.org/wiki/Unum_(number_format)#Posit_(Type_III_Unum) "Unum (number format)").
- Some simple rational numbers (*e.g.*, 1/3 and 1/10) cannot be represented exactly in binary floating point, no matter what the precision is. Using a different radix allows one to represent some of them (*e.g.*, 1/10 in decimal floating point), but the possibilities remain limited. Software packages that perform [rational arithmetic](https://en.wikipedia.org/wiki/Fraction) represent numbers as fractions with integral numerator and denominator, and can therefore represent any rational number exactly. Such packages generally need to use "[bignum](https://en.wikipedia.org/wiki/Bignum)" arithmetic for the individual integers.
- [Interval arithmetic](https://en.wikipedia.org/wiki/Interval_arithmetic) allows one to represent numbers as intervals and obtain guaranteed bounds on results. It is generally based on other arithmetics, in particular floating point.
- [Computer algebra systems](https://en.wikipedia.org/wiki/Computer_algebra_system) such as [Mathematica](https://en.wikipedia.org/wiki/Mathematica), [Maxima](https://en.wikipedia.org/wiki/Maxima_(software) "Maxima (software)"), and [Maple](https://en.wikipedia.org/wiki/Maple_(software) "Maple (software)") can often handle irrational numbers like $\pi$ or ${\sqrt {3}}$ in a completely "formal" way ([symbolic computation](https://en.wikipedia.org/wiki/Symbolic_computation)), without dealing with a specific encoding of the significand. Such a program can evaluate expressions like "$\sin(3\pi )$" exactly, because it is programmed to process the underlying mathematics directly, instead of using approximate values for each intermediate calculation.

## History

![[media/373faff0579b9464e4bad1ac189fe53f1b0a641a.jpg]]
[Leonardo Torres Quevedo](https://en.wikipedia.org/wiki/Leonardo_Torres_Quevedo), in 1914, published an analysis of floating point based on the [analytical engine](https://en.wikipedia.org/wiki/Analytical_engine).

In 1914, the Spanish engineer [Leonardo Torres Quevedo](https://en.wikipedia.org/wiki/Leonardo_Torres_Quevedo) published *Essays on Automatics*, where he designed a special-purpose electromechanical calculator based on [Charles Babbage](https://en.wikipedia.org/wiki/Charles_Babbage)'s [analytical engine](https://en.wikipedia.org/wiki/Analytical_engine) and described a way to store floating-point numbers in a consistent manner. He stated that numbers will be stored in exponential format as *n* × 10$^{m}$, and offered three rules by which consistent manipulation of floating-point numbers by machines could be implemented. For Torres, "*n* will always be the same number of [digits](https://en.wikipedia.org/wiki/Numerical_digit) (e.g. six), the first digit of *n* will be of order of tenths, the second of hundredths, etc, and one will write each quantity in the form: *n*; *m*." The format he proposed shows the need for a fixed-sized significand as is presently used for floating-point data, fixing the location of the decimal point in the significand so that each representation was unique, and how to format such numbers by specifying a syntax to be used that could be entered through a [typewriter](https://en.wikipedia.org/wiki/Typewriter), as was the case of his [Electromechanical Arithmometer](https://en.wikipedia.org/wiki/Leonardo_Torres_y_Quevedo#Analytical_machines) in 1920.

![[media/49caefb21d1e2f2d47c289933c22ad1e46532051.jpg]]
[Konrad Zuse](https://en.wikipedia.org/wiki/Konrad_Zuse), architect of the [Z3](https://en.wikipedia.org/wiki/Z3_(computer)) computer, which uses a 22-bit binary floating-point representation

In 1938, [Konrad Zuse](https://en.wikipedia.org/wiki/Konrad_Zuse) of Berlin completed the [Z1](https://en.wikipedia.org/wiki/Z1_(computer) "Z1 (computer)"), the first binary, programmable [mechanical computer](https://en.wikipedia.org/wiki/Mechanical_computer); it uses a 24-bit binary floating-point number representation with a 7-bit signed exponent, a 17-bit significand (including one implicit bit), and a sign bit. The more reliable [relay](https://en.wikipedia.org/wiki/Relay)-based [Z3](https://en.wikipedia.org/wiki/Z3_(computer) "Z3 (computer)"), completed in 1941, has representations for both positive and negative infinities; in particular, it implements defined operations with infinity, such as $^{1}/_{\infty }=0$, and it stops on undefined operations, such as $0\times \infty$.

Zuse also proposed, but did not complete, carefully rounded floating-point arithmetic that includes $\pm \infty$ and NaN representations, anticipating features of the IEEE Standard by four decades. In contrast, [von Neumann](https://en.wikipedia.org/wiki/John_von_Neumann) recommended against floating-point numbers for the 1951 [IAS machine](https://en.wikipedia.org/wiki/IAS_machine), arguing that fixed-point arithmetic is preferable.

The first *commercial* computer with floating-point hardware was Zuse's [Z4](https://en.wikipedia.org/wiki/Z4_(computer) "Z4 (computer)") computer, designed in 1942–1945. In 1946, Bell Laboratories introduced the [Model V](https://en.wikipedia.org/wiki/Model_V), which implemented [decimal floating-point numbers](https://en.wikipedia.org/wiki/Decimal_floating_point).

The [Pilot ACE](https://en.wikipedia.org/wiki/Pilot_ACE) has binary floating-point arithmetic, and it became operational in 1950 at [National Physical Laboratory, UK](https://en.wikipedia.org/wiki/National_Physical_Laboratory,_UK). Thirty-three were later sold commercially as the [English Electric DEUCE](https://en.wikipedia.org/wiki/English_Electric_DEUCE). The arithmetic is actually implemented in software, but with a one megahertz clock rate, the speed of floating-point and fixed-point operations in this machine were initially faster than those of many competing computers.

The mass-produced [IBM 704](https://en.wikipedia.org/wiki/IBM_704) followed in 1954; it introduced the use of a [biased exponent](https://en.wikipedia.org/wiki/Exponent_bias). For many decades after that, floating-point hardware was typically an optional feature, and computers that had it were said to be "scientific computers", or to have "[scientific computation](https://en.wikipedia.org/wiki/Scientific_computation)" (SC) capability (see also [Extensions for Scientific Computation](https://en.wikipedia.org/wiki/Extensions_for_Scientific_Computation) (XSC)). It was not until the launch of the Intel i486 in 1989 that *general-purpose* personal computers had floating-point capability in hardware as a standard feature.

The [UNIVAC 1100/2200 series](https://en.wikipedia.org/wiki/UNIVAC_1100/2200_series), introduced in 1962, supported two floating-point representations:

- *Single precision*: 36 bits, organized as a 1-bit sign, an 8-bit exponent, and a 27-bit significand.
- *Double precision*: 72 bits, organized as a 1-bit sign, an 11-bit exponent, and a 60-bit significand.

The [IBM 7094](https://en.wikipedia.org/wiki/IBM_7094), also introduced in 1962, supported single-precision and double-precision representations, but with no relation to the UNIVAC's representations. Indeed, in 1964, IBM introduced [hexadecimal floating-point representations](https://en.wikipedia.org/wiki/IBM_hexadecimal_floating-point) in its [System/360](https://en.wikipedia.org/wiki/System/360) mainframes; these same representations are still available for use in modern [z/Architecture](https://en.wikipedia.org/wiki/Z/Architecture) systems. In 1998, IBM implemented IEEE-compatible binary floating-point arithmetic in its mainframes; in 2005, IBM also added IEEE-compatible decimal floating-point arithmetic.

Initially, computers used many different representations for floating-point numbers. The lack of standardization at the mainframe level was an ongoing problem by the early 1970s for those writing and maintaining higher-level source code; these manufacturer floating-point standards differed in the word sizes, the representations, and the rounding behavior and general accuracy of operations. Floating-point compatibility across multiple computing systems was in desperate need of standardization by the early 1980s, leading to the creation of the [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754) standard once the 32-bit (or 64-bit) [word](https://en.wikipedia.org/wiki/Word_(computer_architecture) "Word (computer architecture)") had become commonplace. This standard was significantly based on a proposal from Intel, which was designing the [i8087](https://en.wikipedia.org/wiki/Intel_8087) numerical coprocessor; Motorola, which was designing the [68000](https://en.wikipedia.org/wiki/68000) around the same time, gave significant input as well.

![[media/1c888aaa1247f4e3848f9262368cb1d1441542ea.jpg]]
[William Kahan](https://en.wikipedia.org/wiki/William_Kahan), principal architect of the [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754) floating-point standard

In 1989, mathematician and computer scientist [William Kahan](https://en.wikipedia.org/wiki/William_Kahan) was honored with the [Turing Award](https://en.wikipedia.org/wiki/Turing_Award) for being the primary architect behind this proposal; he was aided by his student Jerome Coonen and a visiting professor, [Harold Stone](https://en.wikipedia.org/wiki/Harold_S._Stone).

Among the x86 (more specifically i8087) innovations are these:

- A precisely specified floating-point representation at the bit-string level, so that all compliant computers interpret bit patterns the same way. This makes it possible to accurately and efficiently transfer floating-point numbers from one computer to another (after accounting for [endianness](https://en.wikipedia.org/wiki/Endianness)).
- A precisely specified behavior for the arithmetic operations: A result is required to be produced as if infinitely precise arithmetic were used to yield a value that is then rounded according to specific rules. This means that a compliant computer program would always produce the same result when given a particular input, thus mitigating the almost mystical reputation that floating-point computation had developed for its hitherto seemingly non-deterministic behavior.
- The ability of [exceptional conditions](https://en.wikipedia.org/wiki/IEEE_754#Exception_handling) (overflow, [divide by zero](https://en.wikipedia.org/wiki/Division_by_zero), etc.) to propagate through a computation in a benign manner and then be handled by the software in a controlled fashion.

These features would be inherited into IEEE 754-1985 (with the exception of the encoding of special values and exceptions), though the extended internal precision of x87 means it requires explicit rounding of exact results directly to the destination precision in order to match standard IEEE 754 results. However, the behavior may not be the same as a rounding to the destination format due to a possible wider exponent range of the extended format.

## Range of floating-point numbers

A floating-point number consists of two [fixed-point](https://en.wikipedia.org/wiki/Fixed-point_arithmetic) components, whose range depends exclusively on the number of bits or digits in their representation. Whereas components linearly depend on their range, the floating-point range linearly depends on the significand range and exponentially on the range of exponent component, which attaches outstandingly wider range to the number.

On a typical computer system, a *[double-precision](https://en.wikipedia.org/wiki/Double-precision_floating-point_format)* (64-bit) binary floating-point number has a coefficient of 53 bits (including 1 implied bit), an exponent of 11 bits, and 1 sign bit. Since 2<sup>10</sup> = 1024, the complete range of the positive normal floating-point numbers in this format is from 2<sup>−1022</sup> ≈ 2 × 10<sup>−308</sup> to approximately 2<sup>1024</sup> ≈ 2 × 10<sup>308</sup>.

The number of normal floating-point numbers in a system (*B*, *P*, *L*, *U*) where

- *B* is the base of the system,
- *P* is the precision of the significand (in base *B*),
- *L* is the smallest exponent of the system,
- *U* is the largest exponent of the system,

is $2\left(B-1\right)\left(B^{P-1}\right)\left(U-L+1\right)$, or $2\left(B-1\right)\left(B^{P-1}\right)\left(U-L+1\right)+1$ considering the value 0.

There is a smallest positive normal floating-point number,

Underflow level = UFL = $B^{L}$,

which has a 1 as the leading digit and 0 for the remaining digits of the significand, and the smallest possible value for the exponent.

There is a largest floating-point number,

Overflow level = OFL = $\left(1-B^{-P}\right)\left(B^{U+1}\right)$,

which has *B* − 1 as the value for each digit of the significand and the largest possible value for the exponent.

In addition, there are representable values strictly between −UFL and UFL. Namely, [positive and negative zeros](https://en.wikipedia.org/wiki/Signed_zero), as well as [subnormal numbers](https://en.wikipedia.org/wiki/Subnormal_number).

## IEEE 754: floating point in modern computers 

The [IEEE](https://en.wikipedia.org/wiki/Institute_of_Electrical_and_Electronics_Engineers) standardized the computer representation for binary floating-point numbers in [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754) (a.k.a. IEC 60559) in 1985. This first standard is followed by almost all modern machines. It was [revised in 2008](https://en.wikipedia.org/wiki/IEEE_754-2008_revision). IBM mainframes support [IBM's own hexadecimal floating point format](https://en.wikipedia.org/wiki/IBM_hexadecimal_floating_point) and IEEE 754-2008 [decimal floating point](https://en.wikipedia.org/wiki/Decimal_floating_point) in addition to the IEEE 754 binary format. The [Cray T90](https://en.wikipedia.org/wiki/Cray_T90) series had an IEEE version, but the [SV1](https://en.wikipedia.org/wiki/Cray_SV1) still uses Cray floating-point format.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

The standard provides for many closely related formats, differing in only a few details. Five of these formats are called *basic formats*, and others are termed *extended precision formats* and *extendable precision format*. Three formats are especially widely used in computer hardware and languages:<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

- [Single precision](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) (binary32), usually used to represent the "float" [type in the C language](https://en.wikipedia.org/wiki/C_data_types#Basic_types) family. This is a binary format that occupies 32 bits (4 bytes) and its significand has a precision of 24 bits (about 7 decimal digits).
- [Double precision](https://en.wikipedia.org/wiki/Double-precision_floating-point_format) (binary64), usually used to represent the "double" [type in the C language](https://en.wikipedia.org/wiki/C_data_types#Basic_types) family. This is a binary format that occupies 64 bits (8 bytes) and its significand has a precision of 53 bits (about 16 decimal digits).
- [Double extended](https://en.wikipedia.org/wiki/Extended_precision), also ambiguously called "extended precision" format. This is a binary format that occupies at least 79 bits (80 if the hidden/implicit bit rule is not used) and its significand has a precision of at least 64 bits (about 19 decimal digits). The [C99](https://en.wikipedia.org/wiki/C99) and [C11](https://en.wikipedia.org/wiki/C11_(C_standard_revision) "C11 (C standard revision)") standards of the C language family, in their annex F ("IEC 60559 floating-point arithmetic"), recommend such an extended format to be provided as "[long double](https://en.wikipedia.org/wiki/Long_double)". A format satisfying the minimal requirements (64-bit significand precision, 15-bit exponent, thus fitting on 80 bits) is provided by the [x86](https://en.wikipedia.org/wiki/X86) architecture. Often on such processors, this format can be used with "long double", though extended precision is not available with MSVC. For [alignment](https://en.wikipedia.org/wiki/Data_structure_alignment) purposes, many tools store this 80-bit value in a 96-bit or 128-bit space. On other processors, "long double" may stand for a larger format, such as quadruple precision, or just double precision, if any form of extended precision is not available.

Increasing the precision of the floating-point representation generally reduces the amount of accumulated [round-off error](https://en.wikipedia.org/wiki/Round-off_error) caused by intermediate calculations. Other IEEE formats include:

- [Decimal64](https://en.wikipedia.org/wiki/Decimal64_floating-point_format) and [decimal128](https://en.wikipedia.org/wiki/Decimal128_floating-point_format) floating-point formats. These formats (especially decimal128) are pervasive in financial transactions because, along with the [decimal32](https://en.wikipedia.org/wiki/Decimal32_floating-point_format) format, they allow correct decimal rounding.
- [Quadruple precision](https://en.wikipedia.org/wiki/Quadruple-precision_floating-point_format#IEEE_754_quadruple-precision_binary_floating-point_format:_binary128) (binary128). This is a binary format that occupies 128 bits (16 bytes) and its significand has a precision of 113 bits (about 34 decimal digits).
- [Half precision](https://en.wikipedia.org/wiki/Half-precision_floating-point_format), also called binary16, a 16-bit floating-point value. It is being used in the NVIDIA [Cg](https://en.wikipedia.org/wiki/Cg_(programming_language)) graphics language, and in the openEXR standard (where it actually predates the introduction in the IEEE 754 standard).

Any integer with absolute value less than 2<sup>24</sup> can be exactly represented in the single-precision format, and any integer with absolute value less than 2<sup>53</sup> can be exactly represented in the double-precision format. Furthermore, a wide range of powers of 2 times such a number can be represented. These properties are sometimes used for purely integer data, to get 53-bit integers on platforms that have double-precision floats but only 32-bit integers.

The standard specifies some special values, and their representation: positive [infinity](https://en.wikipedia.org/wiki/Infinity) (+∞), negative infinity (−∞), a [negative zero](https://en.wikipedia.org/wiki/Negative_zero) (−0) distinct from ordinary ("positive") zero, and "not a number" values ([NaNs](https://en.wikipedia.org/wiki/NaN)).

Comparison of floating-point numbers, as defined by the IEEE standard, is a bit different from usual integer comparison. Negative and positive zero compare equal, and every NaN compares unequal to every value, including itself. All finite floating-point numbers are strictly smaller than +∞ and strictly greater than −∞, and they are ordered in the same way as their values (in the set of real numbers).

### Internal representation

Floating-point numbers are typically packed into a computer datum as the sign bit, the exponent field, and a field for the significand, from left to right. For the [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754) binary formats (basic and extended) that have extant hardware implementations, they are apportioned as follows:

<table class="wikitable" style="text-align:right; border:0">

Format
Bits for the encoding

Exponent<br />
bias
Bits<br />
precision
Number of<br />
decimal digits

Sign
Exponent
Significand
Total

[Half](https://en.wikipedia.org/wiki/Half-precision_floating-point_format) (binary16)
1
5
10
16
15
11
~3.3

[Single](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) (binary32)
1
8
23
32
127
24
~7.2

[Double](https://en.wikipedia.org/wiki/Double-precision_floating-point_format) (binary64)
1
11
52
64
1023
53
~15.9

[x86 extended](https://en.wikipedia.org/wiki/Extended_precision#x86_extended-precision_format)
1
15
64
80
16383
64
~19.2

[Quadruple](https://en.wikipedia.org/wiki/Quadruple-precision_floating-point_format) (binary128)
1
15
112
128
16383
113
~34.0

[Octuple](https://en.wikipedia.org/wiki/Octuple-precision_floating-point_format) (binary256)
1
19
236
256
262143
237
~71.3

</table>

While the exponent can be positive or negative, in binary formats it is stored as an unsigned number that has a fixed "bias" added to it. Values of all 0s in this field are reserved for the zeros and [subnormal numbers](https://en.wikipedia.org/wiki/Subnormal_number); values of all 1s are reserved for the infinities and NaNs. The exponent range for normal numbers is \[−126, 127\] for single precision, \[−1022, 1023\] for double, or \[−16382, 16383\] for quad. Normal numbers exclude subnormal values, zeros, infinities, and NaNs.

In the IEEE binary interchange formats the leading bit of a normalized significand is not actually stored in the computer datum, since it is always 1. It is called the "hidden" or "implicit" bit. Because of this, the single-precision format actually has a significand with 24 bits of precision, the double-precision format has 53, quad has 113, and octuple has 237.

For example, it was shown above that π, rounded to 24 bits of precision, has:

- sign = 0 ; *e* = 1 ; *s* = 110010010000111111011011 (including the hidden bit)

The sum of the exponent bias (127) and the exponent (1) is 128, so this is represented in the single-precision format as

- 0 10000000 10010010000111111011011 (excluding the hidden bit) = 40490FDB as a [hexadecimal](https://en.wikipedia.org/wiki/Hexadecimal) number.

An example of a layout for [32-bit floating point](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) is

![[media/4702b8c86228654a8c4d4c587cf00cc30beec744.png]]

and the [64-bit ("double")](https://en.wikipedia.org/wiki/Double-precision_floating-point_format) layout is similar.

## Other notable floating-point formats

In addition to the widely used [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754) standard formats, other floating-point formats are used, or have been used, in certain domain-specific areas.

- The [Microsoft Binary Format (MBF)](https://en.wikipedia.org/wiki/Microsoft_Binary_Format) was developed for the Microsoft BASIC language products, including Microsoft's first ever product the [Altair BASIC](https://en.wikipedia.org/wiki/Altair_BASIC) (1975), [TRS-80 LEVEL II](https://en.wikipedia.org/wiki/TRS-80), [CP/M](https://en.wikipedia.org/wiki/CP/M)'s [MBASIC](https://en.wikipedia.org/wiki/MBASIC), [IBM PC 5150](https://en.wikipedia.org/wiki/IBM_PC_5150)'s [BASICA](https://en.wikipedia.org/wiki/BASICA), [MS-DOS](https://en.wikipedia.org/wiki/MS-DOS)'s [GW-BASIC](https://en.wikipedia.org/wiki/GW-BASIC) and [QuickBASIC](https://en.wikipedia.org/wiki/QuickBASIC) prior to version 4.00. QuickBASIC version 4.00 and 4.50 switched to the IEEE 754-1985 format but can revert to the MBF format using the /MBF command option. MBF was designed and developed on a simulated [Intel 8080](https://en.wikipedia.org/wiki/Intel_8080) by [Monte Davidoff](https://en.wikipedia.org/wiki/Monte_Davidoff), a dormmate of [Bill Gates](https://en.wikipedia.org/wiki/Bill_Gates), during spring of 1975 for the [MITS Altair 8800](https://en.wikipedia.org/wiki/MITS_Altair_8800). The initial release of July 1975 supported a single-precision (32 bits) format due to cost of the [MITS Altair 8800](https://en.wikipedia.org/wiki/MITS_Altair_8800) 4-kilobytes memory. In December 1975, the 8-kilobytes version added a double-precision (64 bits) format. A single-precision (40 bits) variant format was adopted for other CPU's, notably the [MOS 6502](https://en.wikipedia.org/wiki/MOS_6502) ([Apple II](https://en.wikipedia.org/wiki/Apple_II), [Commodore PET](https://en.wikipedia.org/wiki/Commodore_PET), [Atari](https://en.wikipedia.org/wiki/Atari)), [Motorola 6800](https://en.wikipedia.org/wiki/Motorola_6800) (MITS Altair 680) and [Motorola 6809](https://en.wikipedia.org/wiki/Motorola_6809) ([TRS-80 Color Computer](https://en.wikipedia.org/wiki/TRS-80_Color_Computer)). All Microsoft language products from 1975 through 1987 used the [Microsoft Binary Format](https://en.wikipedia.org/wiki/Microsoft_Binary_Format) until Microsoft adopted the IEEE 754 standard format in all its products starting in 1988 to their current releases. MBF consists of the MBF single-precision format (32 bits, "6-digit BASIC"), the MBF extended-precision format (40 bits, "9-digit BASIC"), and the MBF double-precision format (64 bits); each of them is represented with an 8-bit exponent, followed by a sign bit, followed by a significand of respectively 23, 31, and 55 bits.
- The [bfloat16 format](https://en.wikipedia.org/wiki/Bfloat16_floating-point_format) requires the same amount of memory (16 bits) as the [IEEE 754 half-precision format](https://en.wikipedia.org/wiki/Half-precision_floating-point_format), but allocates 8 bits to the exponent instead of 5, thus providing the same range as a [IEEE 754 single-precision](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) number. The tradeoff is a reduced precision, as the trailing significand field is reduced from 10 to 7 bits. This format is mainly used in the training of [machine learning](https://en.wikipedia.org/wiki/Machine_learning) models, where range is more valuable than precision. Many machine learning accelerators provide hardware support for this format.
- The TensorFloat-32 format combines the 8 bits of exponent of the bfloat16 with the 10 bits of trailing significand field of half-precision formats, resulting in a size of 19 bits. This format was introduced by [Nvidia](https://en.wikipedia.org/wiki/Nvidia), which provides hardware support for it in the Tensor Cores of its [GPUs](https://en.wikipedia.org/wiki/Graphics_processing_unit) based on the Nvidia Ampere architecture. The drawback of this format is its size, which is not a power of 2. However, according to Nvidia, this format should only be used internally by hardware to speed up computations, while inputs and outputs should be stored in the 32-bit single-precision IEEE 754 format.
- The [Hopper](https://en.wikipedia.org/wiki/Hopper_(microarchitecture) "Hopper (microarchitecture)") and [CDNA 3](https://en.wikipedia.org/wiki/CDNA_3) architecture GPUs provide two FP8 formats: one with the same numerical range as half-precision (E5M2) and one with higher precision, but less range (E4M3).
- The [Blackwell](https://en.wikipedia.org/wiki/Blackwell_(microarchitecture) "Blackwell (microarchitecture)") and [CDNA 4](https://en.wikipedia.org/wiki/CDNA_(microarchitecture) "CDNA (microarchitecture)") GPU architecture includes support for FP6 (E3M2 and E2M3) and FP4 (E2M1) formats. FP4 is the smallest floating-point format which allows for all IEEE 754 principles (see [minifloat](https://en.wikipedia.org/wiki/Minifloat)).

|  |  |  |  |  |
|----|----|----|----|----|
| Type | Sign | Exponent | Significand | Total bits |
| FP4 | 1 | 2 | 1 | 4 |
| FP6 (E2M3) | 1 | 2 | 3 | 6 |
| FP6 (E3M2) | 1 | 3 | 2 | 6 |
| FP8 (E4M3) | 1 | 4 | 3 | 8 |
| FP8 (E5M2) | 1 | 5 | 2 | 8 |
| [Half-precision](https://en.wikipedia.org/wiki/Half-precision_floating-point_format) | 1 | 5 | 10 | 16 |
| [bfloat16](https://en.wikipedia.org/wiki/Bfloat16_floating-point_format) | 1 | 8 | 7 | 16 |
| [TensorFloat-32](https://en.wikipedia.org/wiki/TensorFloat-32) | 1 | 8 | 10 | 19 |
| [Single-precision](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) | 1 | 8 | 23 | 32 |
| [Double-precision](https://en.wikipedia.org/wiki/Double-precision_floating-point_format) | 1 | 11 | 52 | 64 |
| [Quadruple-precision](https://en.wikipedia.org/wiki/Quadruple-precision_floating-point_format) | 1 | 15 | 112 | 128 |
| [Octuple-precision](https://en.wikipedia.org/wiki/Octuple-precision_floating-point_format) | 1 | 19 | 236 | 256 |

Comparison of common floating-point formats {.wikitable}

## Representable numbers, conversion and rounding 

By their nature, all numbers expressed in floating-point format are [rational numbers](https://en.wikipedia.org/wiki/Rational_number) with a terminating expansion in the relevant base (for example, a terminating decimal expansion in base-10, or a terminating binary expansion in base-2). Irrational numbers, such as [π](https://en.wikipedia.org/wiki/Pi) or ${\sqrt {2}}$, or non-terminating rational numbers, must be approximated. The number of digits (or bits) of precision also limits the set of rational numbers that can be represented exactly. For example, the decimal number 123456789 cannot be exactly represented if only eight decimal digits of precision are available (it would be rounded to one of the two straddling representable values, 12345678 × 10<sup>1</sup> or 12345679 × 10<sup>1</sup>), the same applies to [non-terminating digits](https://en.wikipedia.org/wiki/Repeating_decimal) (.5 to be rounded to either .55555555 or .55555556).

When a number is represented in some format (such as a character string) which is not a native floating-point representation supported in a computer implementation, then it will require a conversion before it can be used in that implementation. If the number can be represented exactly in the floating-point format then the conversion is exact. If there is not an exact representation then the conversion requires a choice of which floating-point number to use to represent the original value. The representation chosen will have a different value from the original, and the value thus adjusted is called the *rounded value*.

Whether or not a rational number has a terminating expansion depends on the base. For example, in base-10 the number 1/2 has a terminating expansion (0.5) while the number 1/3 does not (0.333...). In base-2 only rationals with denominators that are powers of 2 (such as 1/2 or 3/16) are terminating. Any rational with a denominator that has a prime factor other than 2 will have an infinite binary expansion. This means that numbers that appear to be short and exact when written in decimal format may need to be approximated when converted to binary floating-point. For example, the decimal number 0.1 is not representable in binary floating-point of any finite precision; the exact binary representation would have a "1100" sequence continuing endlessly:

*e* = −4; *s* = 1100110011001100110011001100110011...,

where, as previously, *s* is the significand and *e* is the exponent.

When rounded to 24 bits this becomes

*e* = −4; *s* = 110011001100110011001101,

which is actually 0.100000001490116119384765625 in decimal.

As a further example, the real number [π](https://en.wikipedia.org/wiki/Pi), represented in binary as an infinite sequence of bits is

11.0010010000111111011010101000100010000101101000110000100011010011...

but is

11.0010010000111111011011

when approximated by [rounding](https://en.wikipedia.org/wiki/Rounding) to a precision of 24 bits.

In binary single-precision floating-point, this is represented as *s* = 1.10010010000111111011011 with *e* = 1. This has a decimal value of

**3.141592**7410125732421875,

whereas a more accurate approximation of the true value of π is

**3.14159265358979323846264338327950**...

The result of rounding differs from the true value by about 0.03 parts per million, and matches the decimal representation of π in the first 7 digits. The difference is the [discretization error](https://en.wikipedia.org/wiki/Discretization_error) and is limited by the [machine epsilon](https://en.wikipedia.org/wiki/Machine_epsilon).

The arithmetical difference between two consecutive representable floating-point numbers which have the same exponent is called a [unit in the last place](https://en.wikipedia.org/wiki/Unit_in_the_last_place) (ULP). For example, if there is no representable number lying between the representable numbers 1.45A70C22<sub>16</sub> and 1.45A70C24<sub>16</sub>, the ULP is 2×16<sup>−8</sup>, or 2<sup>−31</sup>. For numbers with a base-2 exponent part of 0, i.e. numbers with an absolute value higher than or equal to 1 but lower than 2, an ULP is exactly 2<sup>−23</sup> or about 10<sup>−7</sup> in single precision, and exactly 2<sup>−53</sup> or about 10<sup>−16</sup> in double precision. The mandated behavior of IEEE-compliant hardware is that the result be within one-half of a ULP.

### Rounding modes

Rounding is used when the exact result of a floating-point operation (or a conversion to floating-point format) would need more digits than there are digits in the significand. IEEE 754 requires *correct rounding*: that is, the rounded result is as if infinitely precise arithmetic was used to compute the value and then rounded (although in implementation only three extra bits are needed to ensure this). There are several different [rounding](https://en.wikipedia.org/wiki/Rounding) schemes (or *rounding modes*). Historically, [truncation](https://en.wikipedia.org/wiki/Truncation) was the typical approach. Since the introduction of IEEE 754, the default method (*[round to nearest, ties to even](https://en.wikipedia.org/wiki/Rounding)*, sometimes called Banker's Rounding) is more commonly used. This method rounds the ideal (infinitely precise) result of an arithmetic operation to the nearest representable value, and gives that representation as the result. In the case of a tie, the value that would make the significand end in an even digit is chosen. The IEEE 754 standard requires the same rounding to be applied to all fundamental algebraic operations, including square root and conversions, when there is a numeric (non-NaN) result. It means that the results of IEEE 754 operations are completely determined in all bits of the result, except for the representation of NaNs. ("Library" functions such as cosine and log are not mandated.)

Alternative rounding options are also available. IEEE 754 specifies the following rounding modes:

- round to nearest, where ties round to the nearest even digit in the required position (the default and by far the most common mode)
- round to nearest, where ties round away from zero (optional for binary floating-point and commonly used in decimal)
- round up (toward +∞; negative results thus round toward zero)
- round down (toward −∞; negative results thus round away from zero)
- round toward zero (truncation; it is similar to the common behavior of float-to-integer conversions, which convert −3.9 to −3 and 3.9 to 3)

Alternative modes are useful when the amount of error being introduced must be bounded. Applications that require a bounded error are multi-precision floating-point, and [interval arithmetic](https://en.wikipedia.org/wiki/Interval_arithmetic). The alternative rounding modes are also useful in diagnosing numerical instability: if the results of a subroutine vary substantially between rounding to + and − infinity then it is likely numerically unstable and affected by round-off error.

### Binary-to-decimal conversion with minimal number of digits

Converting a double-precision binary floating-point number to a decimal string is a common operation, but an algorithm producing results that are both accurate and minimal did not appear in print until 1990, with Steele and White's Dragon4. Some of the improvements since then include:

- David M. Gay's *dtoa.c*, a practical open-source implementation of many ideas in Dragon4.
- Grisu3, with a 4× speedup as it removes the use of [bignums](https://en.wikipedia.org/wiki/Bignum). Must be used with a fallback, as it fails for ~0.5% of cases.
- Errol3, an always-succeeding algorithm similar to, but slower than, Grisu3. Apparently not as good as an early-terminating Grisu with fallback.
- Ryū, an always-succeeding algorithm that is faster and simpler than Grisu3.
- Schubfach, an always-succeeding algorithm that is based on a similar idea to Ryū, developed almost simultaneously and independently. Performs better than Ryū and Grisu3 in certain benchmarks.

Many modern language runtimes use Grisu3 with a Dragon4 fallback.

### Decimal-to-binary conversion

The problem of parsing a decimal string into a binary FP representation is complex, with an accurate parser not appearing until Clinger's 1990 work (implemented in dtoa.c). Further work has likewise progressed in the direction of faster parsing.

## Floating-point operations

For ease of presentation and understanding, decimal [radix](https://en.wikipedia.org/wiki/Radix) with 7 digit precision will be used in the examples, as in the IEEE 754 *decimal32* format. The fundamental principles are the same in any [radix](https://en.wikipedia.org/wiki/Radix) or precision, except that normalization is optional (it does not affect the numerical value of the result). Here, *s* denotes the significand and *e* denotes the exponent.

### Addition and subtraction

A simple method to add floating-point numbers is to first represent them with the same exponent. In the example below, the second number (with the smaller exponent) is shifted right by three digits, and one then proceeds with the usual addition method:

      123456.7 = 1.234567 × 10^5
      101.7654 = 1.017654 × 10^2 = 0.001017654 × 10^5

      Hence:
      123456.7 + 101.7654 = (1.234567 × 10^5) + (1.017654 × 10^2)
                          = (1.234567 × 10^5) + (0.001017654 × 10^5)
                          = (1.234567 + 0.001017654) × 10^5
                          =  1.235584654 × 10^5

In detail:

      e=5;  s=1.234567     (123456.7)
    + e=2;  s=1.017654     (101.7654)

      e=5;  s=1.234567
    + e=5;  s=0.001017654  (after shifting)
    --------------------
      e=5;  s=1.235584654  (true sum: 123558.4654)

This is the true result, the exact sum of the operands. It will be rounded to seven digits and then normalized if necessary. The final result is

      e=5;  s=1.235585    (final sum: 123558.5)

The lowest three digits of the second operand (654) are essentially lost. This is [round-off error](https://en.wikipedia.org/wiki/Round-off_error). In extreme cases, the sum of two non-zero numbers may be equal to one of them:

      e=5;  s=1.234567
    + e=−3; s=9.876543

      e=5;  s=1.234567
    + e=5;  s=0.00000009876543 (after shifting)
    ----------------------
      e=5;  s=1.23456709876543 (true sum)
      e=5;  s=1.234567         (after rounding and normalization)

In the above conceptual examples it would appear that a large number of extra digits would need to be provided by the adder to ensure correct rounding; however, for binary addition or subtraction using careful implementation techniques only a *guard* bit, a *rounding* bit and one extra *sticky* bit need to be carried beyond the precision of the operands.

Another problem of loss of significance occurs when *approximations* to two nearly equal numbers are subtracted. In the following example *e* = 5; *s* = 1.234571 and *e* = 5; *s* = 1.234567 are approximations to the rationals 123457.1467 and 123456.659.

      e=5;  s=1.234571
    − e=5;  s=1.234567
    ----------------
      e=5;  s=0.000004
      e=−1; s=4.000000 (after rounding and normalization)

The floating-point difference is computed exactly because the numbers are close—the [Sterbenz lemma](https://en.wikipedia.org/wiki/Sterbenz_lemma) guarantees this, even in case of underflow when [gradual underflow](https://en.wikipedia.org/wiki/Gradual_underflow) is supported. Despite this, the difference of the original numbers is *e* = −1; *s* = 4.877000, which differs more than 20% from the difference *e* = −1; *s* = 4.000000 of the approximations. In extreme cases, all significant digits of precision can be lost. This *[cancellation](https://en.wikipedia.org/wiki/Catastrophic_cancellation)* illustrates the danger in assuming that all of the digits of a computed result are meaningful. Dealing with the consequences of these errors is a topic in [numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis); see also [Accuracy problems](#Accuracy_problems).

### Multiplication and division

To multiply, the significands are multiplied while the exponents are added, and the result is rounded and normalized.

      e=3;  s=4.734612
    × e=5;  s=5.417242
    -----------------------
      e=8;  s=25.648538980104 (true product)
      e=8;  s=25.64854        (after rounding)
      e=9;  s=2.564854        (after normalization)

Similarly, division is accomplished by subtracting the divisor's exponent from the dividend's exponent, and dividing the dividend's significand by the divisor's significand.

There are no cancellation or absorption problems with multiplication or division, though small errors may accumulate as operations are performed in succession. In practice, the way these operations are carried out in digital logic can be quite complex (see [Booth's multiplication algorithm](https://en.wikipedia.org/wiki/Booth%27s_multiplication_algorithm) and [Division algorithm](https://en.wikipedia.org/wiki/Division_algorithm)).

### Literal syntax

Literals for floating-point numbers depend on languages. They typically use `e` or `E` to denote [scientific notation](https://en.wikipedia.org/wiki/Scientific_notation). The [C programming language](https://en.wikipedia.org/wiki/C_(programming_language) "C (programming language)") and the [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754) standard also define a [hexadecimal literal syntax](https://en.wikipedia.org/wiki/IEEE_754#Hexadecimal_literals) with a base-2 exponent instead of 10. In languages like [C](https://en.wikipedia.org/wiki/C_(programming_language) "C (programming language)"), when the decimal exponent is omitted, a decimal point is needed to differentiate them from integers. Other languages do not have an integer type (such as [JavaScript](https://en.wikipedia.org/wiki/JavaScript)), or allow overloading of numeric types (such as [Haskell](https://en.wikipedia.org/wiki/Haskell_(programming_language))). In these cases, digit strings such as `123` may also be floating-point literals.

Examples of floating-point literals are:

- `99.9`
- `-5000.12`
- `6.02e23`
- `-3e-45`
- `0x1.fffffep+127` in C and IEEE 754

## Dealing with exceptional cases 

Floating-point computation in a computer can run into three kinds of problems:

- An operation can be mathematically undefined, such as ∞/∞, or [division by zero](https://en.wikipedia.org/wiki/Division_by_zero).
- An operation can be legal in principle, but not supported by the specific format, for example, calculating the [square root](https://en.wikipedia.org/wiki/Square_root) of −1 or the inverse sine of 2 (both of which result in [complex numbers](https://en.wikipedia.org/wiki/Complex_number)).
- An operation can be legal in principle, but the result can be impossible to represent in the specified format, because the exponent is too large or too small to encode in the exponent field. Such an event is called an overflow (exponent too large), [underflow](https://en.wikipedia.org/wiki/Arithmetic_underflow) (exponent too small) or [denormalization](https://en.wikipedia.org/wiki/Subnormal_number) (precision loss).

Prior to the IEEE standard, such conditions usually caused the program to terminate, or triggered some kind of [trap](https://en.wikipedia.org/wiki/Trap_(computing)) that the programmer might be able to catch. How this worked was system-dependent, meaning that floating-point programs were not [portable](https://en.wikipedia.org/wiki/Porting).

The term "exception" as used in IEEE 754 is a general term meaning an exceptional condition, which is not necessarily an error, and is a different usage to that typically defined in programming languages such as a C++ or Java, in which an "[exception](https://en.wikipedia.org/wiki/Exception_handling)" is an alternative flow of control, closer to what is termed a "trap" in IEEE 754 terminology. However, in such languages, a control-flow exception such as `ArithmeticException` may still be thrown.

Here, the required default method of handling exceptions according to IEEE 754 is discussed (the IEEE 754 optional trapping and other "alternate exception handling" modes are not discussed). Arithmetic exceptions are (by default) required to be recorded in "sticky" status flag bits. That they are "sticky" means that they are not reset by the next (arithmetic) operation, but stay set until explicitly reset. The use of "sticky" flags thus allows for testing of exceptional conditions to be delayed until after a full floating-point expression or subroutine: without them exceptional conditions that could not be otherwise ignored would require explicit testing immediately after every floating-point operation. By default, an operation always returns a result according to specification without interrupting computation. For instance, 1/0 returns +∞, while also setting the divide-by-zero flag bit (this default of ∞ is designed to often return a finite result when used in subsequent operations and so be safely ignored).

The original IEEE 754 standard, however, failed to recommend operations to handle such sets of arithmetic exception flag bits. So while these were implemented in hardware, initially programming language implementations typically did not provide a means to access them (apart from assembler). Over time some programming language standards (e.g., [C99](https://en.wikipedia.org/wiki/C99)/C11 and Fortran) have been updated to specify methods to access and change status flag bits. The 2008 version of the IEEE 754 standard now specifies a few operations for accessing and handling the arithmetic flag bits. The programming model is based on a single thread of execution and use of them by multiple threads has to be handled by a [means](https://en.wikipedia.org/wiki/Concurrency_(computer_science) "Concurrency (computer science)") outside of the standard (e.g. [C11](https://en.wikipedia.org/wiki/C11_(C_standard_revision) "C11 (C standard revision)") specifies that the flags have [thread-local storage](https://en.wikipedia.org/wiki/Thread-local_storage)).

IEEE 754 specifies five arithmetic exceptions that are to be recorded in the status flags ("sticky bits"):

- **inexact**, set if the rounded (and returned) value is different from the mathematically exact result of the operation.
- **underflow**, set if the rounded value is tiny (as specified in IEEE 754) *and* inexact (or maybe limited to if it has denormalization loss, as per the 1985 version of IEEE 754), returning a subnormal value including the zeros.
- **overflow**, set if the absolute value of the rounded value is too large to be represented. An infinity or maximal finite value is returned, depending on which rounding is used.
- **divide-by-zero**, set if the result is infinite given finite operands, returning an infinity, either +∞ or −∞.
- **invalid**, set if a finite or infinite result cannot be returned e.g. sqrt(−1) or 0/0, returning a quiet NaN.

![[media/2781277e19a3003e003c0cbce143a7859e470910.png]]
Fig. 1: resistances in parallel, with total resistance $R_{tot}$

The default return value for each of the exceptions is designed to give the correct result in the majority of cases such that the exceptions can be ignored in the majority of codes. *inexact* returns a correctly rounded result, and *underflow* returns a value less than or equal to the smallest positive normal number in magnitude and can almost always be ignored. *divide-by-zero* returns infinity exactly, which will typically then divide a finite number and so give zero, or else will give an *invalid* exception subsequently if not, and so can also typically be ignored. For example, the effective resistance of n resistors in parallel (see fig. 1) is given by $R_{\text{tot}}=1/(1/R_{1}+1/R_{2}+\cdots +1/R_{n})$. If a short-circuit develops with $R_{1}$ set to 0, $1/R_{1}$ will return +infinity which will give a final $R_{tot}$ of 0, as expected (see the continued fraction example of [IEEE 754 design rationale](https://en.wikipedia.org/wiki/Floating_point#IEEE_754:_floating_point_in_modern_computers) for another example).

*Overflow* and *invalid* exceptions can typically not be ignored, but do not necessarily represent errors: for example, a [root-finding](https://en.wikipedia.org/wiki/Zero_of_a_function) routine, as part of its normal operation, may evaluate a passed-in function at values outside of its domain, returning NaN and an *invalid* exception flag to be ignored until finding a useful start point.

## Accuracy problems

The fact that floating-point numbers cannot accurately represent all real numbers, and that floating-point operations cannot accurately represent true arithmetic operations, leads to many surprising situations. This is related to the finite [precision](https://en.wikipedia.org/wiki/Precision_(computer_science) "Precision (computer science)") with which computers generally represent numbers.

For example, the decimal numbers 0.1 and 0.01 cannot be represented exactly as binary floating-point numbers. In the IEEE 754 binary32 format with its 24-bit significand, the result of attempting to square the approximation to 0.1 is neither 0.01 nor the representable number closest to it. The decimal number 0.1 is represented in binary as `e` = −4; `s` = 110011001100110011001101, which is

0.100000001490116119384765625 exactly.

Squaring this number gives

0.010000000298023226097399174250313080847263336181640625 exactly.

Squaring it with rounding to the 24-bit precision gives

0.010000000707805156707763671875 exactly.

But the representable number closest to 0.01 is

0.009999999776482582092285156250 exactly.

Also, the non-representability of π (and π/2) means that an attempted computation of tan(π/2) will not yield a result of infinity, nor will it even overflow in the usual floating-point formats (assuming an accurate implementation of tan). It is simply not possible for standard floating-point hardware to attempt to compute tan(π/2), because π/2 cannot be represented exactly. This computation in C:

    // Enough digits to be sure we get the correct approximation.
    const double pi = 3.1415926535897932384626433832795;
    double z = tan(pi / 2.0);

will give a result of 16331239353195370.0. In single precision (using the `tanf` function), the result will be −22877332.0.

By the same token, an attempted computation of sin(π) will not yield zero. The result will be (approximately) 0.1225×10<sup>−15</sup> in double precision, or −0.8742×10<sup>−7</sup> in single precision.

While floating-point addition and multiplication are both [commutative](https://en.wikipedia.org/wiki/Commutative) (`a` + `b` = `b` + `a` and `a` × `b` = `b` × `a`), they are not necessarily [associative](https://en.wikipedia.org/wiki/Associative_property). That is, (`a` + `b`) + `c` is not necessarily equal to `a` + (`b` + `c`). Using 7-digit significand decimal arithmetic:

     a = 1234.567, b = 45.67834, c = 0.0004

     (a + b) + c:
         1234.567   (a)
       +   45.67834 (b)
       ____________
         1280.24534   rounds to   1280.245

        1280.245  (a + b)
       +   0.0004 (c)
       ____________
        1280.2454   rounds to   1280.245  ← (a + b) + c

     a + (b + c):
       45.67834 (b)
     +  0.0004  (c)
     ____________
       45.67874

       1234.567   (a)
     +   45.67874   (b + c)
     ____________
       1280.24574   rounds to   1280.246 ← a + (b + c)

They are also not necessarily [distributive](https://en.wikipedia.org/wiki/Distributive_property). That is, (`a` + `b`) × `c` may not be the same as `a` × `c` + `b` × `c`:

     1234.567 × 3.333333 = 4115.223
     1.234567 × 3.333333 = 4.115223
                           4115.223 + 4.115223 = 4119.338
     but
     1234.567 + 1.234567 = 1235.802
                           1235.802 × 3.333333 = 4119.340

In addition to loss of significance, inability to represent numbers such as π and 0.1 exactly, and other slight inaccuracies, the following phenomena may occur:

- [Cancellation](https://en.wikipedia.org/wiki/Catastrophic_cancellation): subtraction of nearly equal operands may cause extreme loss of accuracy. When we subtract two almost equal numbers we set the most significant digits to zero, leaving ourselves with just the insignificant, and most erroneous, digits. For example, when determining a [derivative](https://en.wikipedia.org/wiki/Derivative) of a function the following formula is used:

$$
Q(h)={\frac {f(a+h)-f(a)}{h}}.
$$

  Intuitively one would want an `h` very close to zero; however, when using floating-point operations, the smallest number will not give the best approximation of a derivative. As `h` grows smaller, the difference between `f`(`a` + `h`) and `f`(`a`) grows smaller, cancelling out the most significant and least erroneous digits and making the most erroneous digits more important. As a result the smallest number of `h` possible will give a more erroneous approximation of a derivative than a somewhat larger number. This is perhaps the most common and serious accuracy problem.

- Conversions to integer are not intuitive: converting (63.0/9.0) to integer yields 7, but converting (0.63/0.09) may yield 6. This is because conversions generally truncate rather than round. [Floor and ceiling functions](https://en.wikipedia.org/wiki/Floor_and_ceiling_functions) may produce answers which are off by one from the intuitively expected value.

- Limited exponent range: results might overflow yielding infinity, or underflow yielding a [subnormal number](https://en.wikipedia.org/wiki/Subnormal_number) or zero. In these cases precision will be lost.

- Testing for [safe division](https://en.wikipedia.org/wiki/Division_by_zero#Computer_arithmetic) is problematic: Checking that the divisor is not zero does not guarantee that a division will not overflow.

- Testing for equality is problematic. Two computational sequences that are mathematically equal may well produce different floating-point values.

### Incidents

- On 25 February 1991, a [loss of significance](https://en.wikipedia.org/wiki/Loss_of_significance) in a [MIM-104 Patriot](https://en.wikipedia.org/wiki/MIM-104_Patriot) missile battery [prevented it from intercepting](https://en.wikipedia.org/wiki/MIM-104_Patriot#Failure_at_Dhahran) an incoming [Scud](https://en.wikipedia.org/wiki/Al_Hussein_(missile)) missile in [Dhahran](https://en.wikipedia.org/wiki/Dhahran), [Saudi Arabia](https://en.wikipedia.org/wiki/Saudi_Arabia), contributing to the death of 28 soldiers from the U.S. Army's [14th Quartermaster Detachment](https://en.wikipedia.org/wiki/14th_Quartermaster_Detachment). The weapons control computer counted time in an integer number of tenths of a second since boot. For conversion to a floating-point number of seconds in velocity and position calculations, the software originally multiplied this number by a 24-bit [fixed-point](https://en.wikipedia.org/wiki/Fixed-point_arithmetic) binary approximation to 0.1, specifically 

$$
0.00011001100110011001100_{2}=0.1\times (1-2^{-20}).
$$

 Some parts of the software were later adapted to use a more accurate conversion to floating-point, but some parts were not updated and still used the 24-bit approximation. These parts of the software drifted from one another by about 3.43 milliseconds per hour. After 20 hours, the discrepancy of about 68.7 ms was enough for the radar tracking system to lose track of Scuds; the control system in the Dhahran missile battery had been running for about 100 hours when it failed to track and intercept an incoming Scud. The failure to intercept arose not from using floating point specifically, but from subtracting two different approximations to unit conversion with different errors when representing time, so the unit conversion error in the difference did not cancel out but rather grew indefinitely with uptime.
- [Salami slicing](https://en.wikipedia.org/wiki/Salami_slicing_tactics#Financial_schemes) is the practice of removing the 'invisible' part of a transaction into a separate account.<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup>

### Machine precision and backward error analysis

*Machine precision* is a quantity that characterizes the accuracy of a floating-point system, and is used in [backward error analysis](https://en.wikipedia.org/wiki/Error_analysis_(mathematics)#Error_analysis_in_numerical_modeling "Error analysis (mathematics)") of floating-point algorithms. It is also known as unit roundoff or *[machine epsilon](https://en.wikipedia.org/wiki/Machine_epsilon)*. Usually denoted `Ε`<sub>mach</sub>, its value depends on the particular rounding being used.

With rounding to zero, 

$$
\mathrm {E} _{\text{mach}}=B^{1-P},\,
$$

 whereas rounding to nearest, 

$$
\mathrm {E} _{\text{mach}}={\tfrac {1}{2}}B^{1-P},
$$

 where *B* is the base of the system and *P* is the precision of the significand (in base *B*).

This is important since it bounds the *[relative error](https://en.wikipedia.org/wiki/Relative_error)* in representing any non-zero real number `x` within the normalized range of a floating-point system: 

$$
\left|{\frac {\operatorname {fl} (x)-x}{x}}\right|\leq \mathrm {E} _{\text{mach}}.
$$

Backward error analysis, the theory of which was developed and popularized by [James H. Wilkinson](https://en.wikipedia.org/wiki/James_H._Wilkinson), can be used to establish that an algorithm implementing a numerical function is numerically stable. The basic approach is to show that although the calculated result, due to roundoff errors, will not be exactly correct, it is the exact solution to a nearby problem with slightly perturbed input data. If the perturbation required is small, on the order of the uncertainty in the input data, then the results are in some sense as accurate as the data "deserves". The algorithm is then defined as *[[Numerical Stability|backward stable]]*. Stability is a measure of the sensitivity to rounding errors of a given numerical procedure; by contrast, the [[Condition Number]] of a function for a given problem indicates the inherent sensitivity of the function to small perturbations in its input and is independent of the implementation used to solve the problem.

As a trivial example, consider a simple expression giving the inner product of (length two) vectors $x$ and $y$, then 

$$
{\begin{aligned}\operatorname {fl} (x\cdot y)&=\operatorname {fl} {\big (}\operatorname {fl} (x_{1}\cdot y_{1})+\operatorname {fl} (x_{2}\cdot y_{2}){\big )},&&{\text{ where }}\operatorname {fl} (){\text{ indicates correctly rounded floating-point arithmetic}}\\&=\operatorname {fl} {\big (}(x_{1}\cdot y_{1})(1+\delta _{1})+(x_{2}\cdot y_{2})(1+\delta _{2}){\big )},&&{\text{ where }}\delta _{n}\leq \mathrm {E} _{\text{mach}},{\text{ from above}}\\&={\big (}(x_{1}\cdot y_{1})(1+\delta _{1})+(x_{2}\cdot y_{2})(1+\delta _{2}){\big )}(1+\delta _{3})\\&=(x_{1}\cdot y_{1})(1+\delta _{1})(1+\delta _{3})+(x_{2}\cdot y_{2})(1+\delta _{2})(1+\delta _{3}),\end{aligned}}
$$

 and so 

$$
\operatorname {fl} (x\cdot y)={\hat {x}}\cdot {\hat {y}},
$$

where

$$
{\begin{aligned}{\hat {x}}_{1}&=x_{1}(1+\delta _{1});&{\hat {x}}_{2}&=x_{2}(1+\delta _{2});\\{\hat {y}}_{1}&=y_{1}(1+\delta _{3});&{\hat {y}}_{2}&=y_{2}(1+\delta _{3}),\\\end{aligned}}
$$

where

$$
\delta _{n}\leq \mathrm {E} _{\text{mach}}
$$

by definition, which is the sum of two slightly perturbed (on the order of Ε<sub>mach</sub>) input data, and so is backward stable. For more realistic examples in [numerical linear algebra](https://en.wikipedia.org/wiki/Numerical_linear_algebra), see Higham 2002 and other references below.

### Minimizing the effect of accuracy problems

Although individual arithmetic operations of IEEE 754 are guaranteed accurate to within half a [ULP](https://en.wikipedia.org/wiki/Unit_in_the_last_place), more complicated formulae can suffer from larger errors for a variety of reasons. The loss of accuracy can be substantial if a problem or its data are [[Condition Number|ill-conditioned]], meaning that the correct result is hypersensitive to tiny perturbations in its data. However, even functions that are well-conditioned can suffer from large loss of accuracy if an algorithm [[Numerical Stability|numerically unstable]] for that data is used: apparently equivalent formulations of expressions in a programming language can differ markedly in their numerical stability. One approach to remove the risk of such loss of accuracy is the design and analysis of numerically stable algorithms, which is an aim of the branch of mathematics known as [numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis). Another approach that can protect against the risk of numerical instabilities is the computation of intermediate (scratch) values in an algorithm at a higher precision than the final result requires, which can remove, or reduce by orders of magnitude, such risk: [IEEE 754 quadruple precision](https://en.wikipedia.org/wiki/Quadruple-precision_floating-point_format) and [extended precision](https://en.wikipedia.org/wiki/Extended_precision) are designed for this purpose when computing at double precision.

For example, the following algorithm is a direct implementation to compute the function $f(x)={\frac {x-1}{\exp(x-1)-1}}$, which is well-conditioned at $x=1$. However, it can be shown to be numerically unstable and lose up to half the significant digits carried by the arithmetic when computed near 1.0.

    #include <math.h>

    double f(double x)
    {
        double y = x - 1.0;
        double z = exp(y);
        if (z != 1.0) {
            z = y / (z - 1.0);
        }
        return z;
    }

A numerical analysis of the algorithm reveals that if the following non-obvious change to the line `z = y / (z - 1.0);` is made:

    z = log(z) / (z - 1.0);

then the algorithm becomes numerically stable and can compute to full double precision.

To maintain the properties of such carefully constructed numerically stable programs, careful handling by the [compiler](https://en.wikipedia.org/wiki/Compiler) is required. Certain "optimizations" that compilers might make (for example, reordering operations) can work against the goals of well-behaved software. There is some controversy about the failings of compilers and language designs in this area: C99 is an example of a language where such optimizations are carefully specified to maintain numerical precision. See the external references at the bottom of this article.

A detailed treatment of the techniques for writing high-quality floating-point software is beyond the scope of this article, and the reader is referred to, and the other references at the bottom of this article. Kahan suggests several rules of thumb that can substantially decrease by orders of magnitude the risk of numerical anomalies, in addition to, or in lieu of, a more careful numerical analysis. These include: as noted above, computing all expressions and intermediate results in the highest precision supported in hardware (a common rule of thumb is to carry twice the precision of the desired result, i.e. compute in double precision for a final single-precision result, or in double extended or quad precision for up to double-precision results); and rounding input data and results to only the precision required and supported by the input data (carrying excess precision in the final result beyond that required and supported by the input data can be misleading, increases storage cost and decreases speed, and the excess bits can affect convergence of numerical procedures: notably, the first form of the iterative example given below converges correctly when using this rule of thumb). Brief descriptions of several additional issues and techniques follow.

As decimal fractions can often not be exactly represented in binary floating-point, such arithmetic is at its best when it is simply being used to measure real-world quantities over a wide range of scales (such as the orbital period of a moon around Saturn or the mass of a [proton](https://en.wikipedia.org/wiki/Proton)), and at its worst when it is expected to model the interactions of quantities expressed as decimal strings that are expected to be exact. An example of the latter case is financial calculations. For this reason, financial software tends not to use a binary floating-point number representation. The "decimal" data type of the [C#](https://en.wikipedia.org/wiki/C_Sharp_(programming_language) "C Sharp (programming language)") and [Python](https://en.wikipedia.org/wiki/Python_(programming_language) "Python (programming language)") programming languages, and the decimal formats of the [IEEE 754-2008](https://en.wikipedia.org/wiki/IEEE_754-2008) standard, are designed to avoid the problems of binary floating-point representations when applied to human-entered exact decimal values, and make the arithmetic always behave as expected when numbers are printed in decimal.

Expectations from mathematics may not be realized in the field of floating-point computation. For example, it is known that $(x+y)(x-y)=x^{2}-y^{2}\,$, and that $\sin ^{2}{\theta }+\cos ^{2}{\theta }=1\,$. However, these facts cannot be relied on when the quantities involved are the result of floating-point computation.

The use of the equality test (`if (x==y) ...`) requires care when dealing with floating-point numbers. Even simple expressions like `0.6 / 0.2 - 3 == 0` will, on most computers, fail to be true (in IEEE 754 double precision, for example, `0.6 / 0.2 - 3` is approximately equal to −4.44089209850063×10<sup>−16</sup>). Consequently, such tests are sometimes replaced with "fuzzy" comparisons (`if (abs(x-y) < epsilon) ...`, where epsilon is sufficiently small and tailored to the application, such as 1.0E−13). The wisdom of doing this varies greatly, and can require numerical analysis to bound epsilon. Values derived from the primary data representation and their comparisons should be performed in a wider, extended, precision to minimize the risk of such inconsistencies due to round-off errors. It is often better to organize the code in such a way that such tests are unnecessary. For example, in [computational geometry](https://en.wikipedia.org/wiki/Computational_geometry), exact tests of whether a point lies off or on a line or plane defined by other points can be performed using adaptive precision or exact arithmetic methods.

Small errors in floating-point arithmetic can grow when mathematical algorithms perform operations an enormous number of times. A few examples are [matrix inversion](https://en.wikipedia.org/wiki/Matrix_inversion), [eigenvector](https://en.wikipedia.org/wiki/Eigenvector) computation, and differential equation solving. These algorithms must be very carefully designed, using numerical approaches such as [iterative refinement](https://en.wikipedia.org/wiki/Iterative_refinement), if they are to work well.

Summation of a vector of floating-point values is a basic algorithm in [scientific computing](https://en.wikipedia.org/wiki/Computational_science), and so an awareness of when loss of significance can occur is essential. For example, if one is adding a very large number of numbers, the individual addends are very small compared with the sum. This can lead to loss of significance. A typical addition would then be something like

    3253.671
    +  3.141276
    -----------
    3256.812

The low 3 digits of the addends are effectively lost. Suppose, for example, that one needs to add many numbers, all approximately equal to 3. After 1000 of them have been added, the running sum is about 3000; the lost digits are not regained. The [Kahan summation algorithm](https://en.wikipedia.org/wiki/Kahan_summation_algorithm) may be used to reduce the errors.

Round-off error can affect the convergence and accuracy of iterative numerical procedures. As an example, [Archimedes](https://en.wikipedia.org/wiki/Archimedes) approximated π by calculating the perimeters of polygons [inscribing](https://en.wikipedia.org/wiki/Inscribed_figure) and [circumscribing](https://en.wikipedia.org/wiki/Circumscribing) a circle, starting with hexagons, and successively doubling the number of sides. As noted above, computations may be rearranged in a way that is mathematically equivalent but less prone to error ([numerical analysis](https://en.wikipedia.org/wiki/Numerical_analysis)). Two forms of the recurrence formula for the circumscribed polygon are:<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

- $t_{0}={\frac {1}{\sqrt {3}}}$
- First form: $t_{i+1}={\frac {{\sqrt {t_{i}^{2}+1}}-1}{t_{i}}}$
- Second form: $t_{i+1}={\frac {t_{i}}{{\sqrt {t_{i}^{2}+1}}+1}}$
- $\pi \sim 6\times 2^{i}\times t_{i}$, converging as $i\rightarrow \infty$

Here is a computation using IEEE "double" (a significand with 53 bits of precision) arithmetic:

     i   6 × 2i × ti, first form    6 × 2i × ti, second form
    ---------------------------------------------------------
     0   3.4641016151377543863      3.4641016151377543863
     1   3.2153903091734710173      3.2153903091734723496
     2   3.1596599420974940120      3.1596599420975006733
     3   3.1460862151314012979      3.1460862151314352708
     4   3.1427145996453136334      3.1427145996453689225
     5   3.1418730499801259536      3.1418730499798241950
     6   3.1416627470548084133      3.1416627470568494473
     7   3.1416101765997805905      3.1416101766046906629
     8   3.1415970343230776862      3.1415970343215275928
     9   3.1415937488171150615      3.1415937487713536668
    10   3.1415929278733740748      3.1415929273850979885
    11   3.1415927256228504127      3.1415927220386148377
    12   3.1415926717412858693      3.1415926707019992125
    13   3.1415926189011456060      3.1415926578678454728
    14   3.1415926717412858693      3.1415926546593073709
    15   3.1415919358822321783      3.1415926538571730119
    16   3.1415926717412858693      3.1415926536566394222
    17   3.1415810075796233302      3.1415926536065061913
    18   3.1415926717412858693      3.1415926535939728836
    19   3.1414061547378810956      3.1415926535908393901
    20   3.1405434924008406305      3.1415926535900560168
    21   3.1400068646912273617      3.1415926535898608396
    22   3.1349453756585929919      3.1415926535898122118
    23   3.1400068646912273617      3.1415926535897995552
    24   3.2245152435345525443      3.1415926535897968907
    25                              3.1415926535897962246
    26                              3.1415926535897962246
    27                              3.1415926535897962246
    28                              3.1415926535897962246
                  The true value is 3.14159265358979323846264338327...

While the two forms of the recurrence formula are clearly mathematically equivalent, the first subtracts 1 from a number extremely close to 1, leading to an increasingly problematic loss of [significant digits](https://en.wikipedia.org/wiki/Significant_digit). As the recurrence is applied repeatedly, the accuracy improves at first, but then it deteriorates. It never gets better than about 8 digits, even though 53-bit arithmetic should be capable of about 16 digits of precision. When the second form of the recurrence is used, the value converges to 15 digits of precision.

### "Fast math" optimization

The aforementioned lack of [associativity](https://en.wikipedia.org/wiki/Associative_property) of floating-point operations in general means that [compilers](https://en.wikipedia.org/wiki/Compilers) cannot as effectively reorder arithmetic expressions as they could with integer and fixed-point arithmetic, presenting a roadblock in optimizations such as [common subexpression elimination](https://en.wikipedia.org/wiki/Common_subexpression_elimination) and auto-[vectorization](https://en.wikipedia.org/wiki/Single_instruction,_multiple_data). The "fast math" option on many compilers (ICC, GCC, Clang, MSVC...) turns on reassociation along with unsafe assumptions such as a lack of NaN and infinite numbers in IEEE 754. Some compilers also offer more granular options to only turn on reassociation or to mark specific regions of code for more aggressive optimization. In either case, the programmer is exposed to many of the precision pitfalls mentioned above for the portion of the program using "fast" math.

In some compilers (GCC and Clang \[when a GCC installation is present\]), turning on "fast" math may cause the program to [disable subnormal floats](https://en.wikipedia.org/wiki/Subnormal_number#Disabling_subnormal_floats_at_the_code_level) at startup, affecting the floating-point behavior of not only the generated code, but also any program using such code as a [library](https://en.wikipedia.org/wiki/Library_(computing) "Library (computing)"). This was fixed in GCC 13.

In most [Fortran](https://en.wikipedia.org/wiki/Fortran) compilers, as allowed by the ISO/IEC 1539-1:2004 Fortran standard, reassociation is the default, with breakage largely prevented by the "protect parens" setting (also on by default). This setting stops the compiler from reassociating beyond the boundaries of parentheses. [Intel Fortran Compiler](https://en.wikipedia.org/wiki/Intel_Fortran_Compiler) is a notable outlier.

A common problem in "fast" math is that subexpressions may not be optimized identically from place to place, leading to unexpected differences. One interpretation of the issue is that "fast" math as implemented currently has a poorly defined semantics. One attempt at formalizing "fast" math optimizations is seen in *Icing*, a verified compiler.

## See also

- [Arbitrary-precision arithmetic](https://en.wikipedia.org/wiki/Arbitrary-precision_arithmetic)
- [C99](https://en.wikipedia.org/wiki/C99#IEEE_754_floating-point_support) for code examples demonstrating access and use of IEEE 754 features.
- [Computable number](https://en.wikipedia.org/wiki/Computable_number)
- [Coprocessor](https://en.wikipedia.org/wiki/Coprocessor)
- [Decimal floating point](https://en.wikipedia.org/wiki/Decimal_floating_point)
- [Double-precision floating-point format](https://en.wikipedia.org/wiki/Double-precision_floating-point_format)
- [Experimental mathematics](https://en.wikipedia.org/wiki/Experimental_mathematics) – utilizes high precision floating-point computations
- [Fixed-point arithmetic](https://en.wikipedia.org/wiki/Fixed-point_arithmetic)
- [Floating-point error mitigation](https://en.wikipedia.org/wiki/Floating-point_error_mitigation)
- [Floating origin](https://en.wikipedia.org/wiki/Floating_origin) – a technique in 3D rendering to mitigate precision loss of floating-point formats
- [FLOPS](https://en.wikipedia.org/wiki/FLOPS)
- [Gal's accurate tables](https://en.wikipedia.org/wiki/Gal%27s_accurate_tables)
- [GNU MPFR](https://en.wikipedia.org/wiki/GNU_MPFR)
- [Half-precision floating-point format](https://en.wikipedia.org/wiki/Half-precision_floating-point_format)
- [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754) – Standard for Binary Floating-Point Arithmetic
- [IBM Floating Point Architecture](https://en.wikipedia.org/wiki/IBM_hexadecimal_floating-point)
- [Kahan summation algorithm](https://en.wikipedia.org/wiki/Kahan_summation_algorithm)
- [Microsoft Binary Format](https://en.wikipedia.org/wiki/Microsoft_Binary_Format) (MBF)
- [Minifloat](https://en.wikipedia.org/wiki/Minifloat)
- [Q (number format)](https://en.wikipedia.org/wiki/Q_(number_format) "Q (number format)") for constant resolution
- [Quadruple-precision floating-point format](https://en.wikipedia.org/wiki/Quadruple-precision_floating-point_format) (including double-double)
- [Significant figures](https://en.wikipedia.org/wiki/Significant_figures)
- [Single-precision floating-point format](https://en.wikipedia.org/wiki/Single-precision_floating-point_format)
- [Standard Apple Numerics Environment (SANE)](https://en.wikipedia.org/wiki/Standard_Apple_Numerics_Environment)

## Notes

1.  The *[significand](https://en.wikipedia.org/wiki/Significand)* of a floating-point number is also called *mantissa* by some authors—not to be confused with the [mantissa](https://en.wikipedia.org/wiki/Mantissa_(logarithm)) of a [logarithm](https://en.wikipedia.org/wiki/Logarithm). Somewhat vague, terms such as *coefficient* or *argument* are also used by some. The usage of the term *fraction* by some authors is potentially misleading as well. The term *characteristic* (as used e.g. by [CDC](https://en.wikipedia.org/wiki/Control_Data_Corporation)) is ambiguous, as it was historically also used to specify some form of [exponent](#NB-Exponent) of floating-point numbers.
2.  The *[exponent](https://en.wikipedia.org/wiki/Exponent)* of a floating-point number is sometimes also referred to as *scale*. The term *characteristic* (for *[biased exponent](https://en.wikipedia.org/wiki/Biased_exponent)*, *exponent bias*, or *excess n representation*) is ambiguous, as it was historically also used to specify the [significand](#NB-Significand) of floating-point numbers.
4.  Octal (base-8) floating-point arithmetic is used in the [Ferranti Atlas](https://en.wikipedia.org/wiki/Ferranti_Atlas) (1962), [Burroughs B5500](https://en.wikipedia.org/wiki/Burroughs_B5500) (1964), [Burroughs B5700](https://en.wikipedia.org/wiki/Burroughs_B5700) (1971), [Burroughs B6700](https://en.wikipedia.org/wiki/Burroughs_B6700) (1971) and [Burroughs B7700](https://en.wikipedia.org/wiki/Burroughs_B7700) (1972) computers.
5.  Quaternary (base-4) floating-point arithmetic is used in the [Illinois ILLIAC II](https://en.wikipedia.org/wiki/Illinois_ILLIAC_II) (1962) computer. It is also used in the Digital Field System DFS IV and V high-resolution site survey systems.
6.  Base-256 floating-point arithmetic is used in the [Rice Institute R1](https://en.wikipedia.org/wiki/Rice_Institute_R1) computer (since 1958).
7.  Base-65536 floating-point arithmetic is used in the [MANIAC II](https://en.wikipedia.org/wiki/MANIAC_II) (1956) computer.
8.  Computer hardware does not necessarily compute the exact value; it simply has to produce the equivalent rounded result as though it had computed the infinitely precise result.
9.  The enormous complexity of modern [division algorithms](https://en.wikipedia.org/wiki/Division_algorithm) once led to a famous error. An early version of the [Intel Pentium](https://en.wikipedia.org/wiki/Intel_Pentium) chip was shipped with a [division instruction](https://en.wikipedia.org/wiki/FDIV) that, on rare occasions, gave slightly incorrect results. Many computers had been shipped before the error was discovered. Until the defective computers were replaced, patched versions of compilers were developed that could avoid the failing cases. See *[Pentium FDIV bug](https://en.wikipedia.org/wiki/Pentium_FDIV_bug)*.
10. But an attempted computation of $\cos(\pi )$ yields $-1$ exactly. Since the derivative is nearly zero near $\pi$, the effect of the inaccuracy in the argument is far smaller than the spacing of the floating-point numbers around $-1$, and the rounded result is exact.
11. [William Kahan](https://en.wikipedia.org/wiki/William_Morton_Kahan) notes: "Except in extremely uncommon situations, extra-precise arithmetic generally attenuates risks due to roundoff at far less cost than the price of a competent error-analyst."
12. The [Taylor expansion](https://en.wikipedia.org/wiki/Taylor_expansion) of this function demonstrates that it is well-conditioned near $x=1$: $f(x)=1-{\frac {x-1}{2}}+{\frac {(x-1)^{2}}{12}}-{\frac {(x-1)^{4}}{720}}+{\frac {(x-1)^{6}}{30240}}-{\frac {(x-1)^{8}}{1209600}}+\cdots$ for $|x-1|<\pi$.
13. The equivalence of the two forms can be verified algebraically by noting that the [denominator](https://en.wikipedia.org/wiki/Denominator) of the fraction in the second form is the [conjugate](https://en.wikipedia.org/wiki/Conjugate_(algebra)) of the [numerator](https://en.wikipedia.org/wiki/Numerator) of the first. By multiplying the top and bottom of the first expression by this conjugate, one obtains the second expression.

## References

1.  ^       Muller, Jean-Michel; Brisebarre, Nicolas; de Dinechin, Florent; Jeannerod, Claude-Pierre; Lefèvre, Vincent; Melquiond, Guillaume; [Revol, Nathalie](https://en.wikipedia.org/wiki/Nathalie_Revol); Stehlé, Damien; Torres, Serge (2010). [Handbook of Floating-Point Arithmetic](https://books.google.com/books?id=baFvrIOPvncC&pg=PA16) (1st ed.). [Birkhäuser](https://en.wikipedia.org/wiki/Birkh%C3%A4user). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-0-8176-4705-6](https://doi.org/10.1007%2F978-0-8176-4705-6). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8176-4704-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8176-4704-9). [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [2009939668](https://lccn.loc.gov/2009939668).
2.  ^   Sterbenz, Pat H. (1974). [Floating-Point Computation](https://archive.org/details/SterbenzFloatingPointComputation/mode/2up). Englewood Cliffs, NJ, United States: Prentice-Hall. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-13-322495-3](https://en.wikipedia.org/wiki/Special:BookSources/0-13-322495-3).
3.  Smith, Steven W. (1997). ["Chapter 28, Fixed versus Floating Point"](http://www.dspguide.com/ch28/4.htm). *The Scientist and Engineer's Guide to Digital Signal Processing*. California Technical Pub. p. 514. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-9660176-3-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-9660176-3-2). Retrieved 2012-12-31.
4.  ^   Zehendner, Eberhard (Summer 2008). ["Rechnerarithmetik: Fest- und Gleitkommasysteme"](https://users.fmi.uni-jena.de/~nez/rechnerarithmetik_5/folien/Rechnerarithmetik.2008.05.handout.pdf) (PDF) (Lecture script) (in German). [Friedrich-Schiller-Universität Jena](https://en.wikipedia.org/wiki/Friedrich-Schiller-Universit%C3%A4t_Jena). p. 2. [Archived](https://web.archive.org/web/20180807062449/https://users.fmi.uni-jena.de/~nez/rechnerarithmetik_5/folien/Rechnerarithmetik.2008.05.handout.pdf) (PDF) from the original on 2018-08-07. Retrieved 2018-08-07. [1](https://en.wikipedia.org/wiki/1)(https://web.archive.org/web/20180806175620/https://users.fmi.uni-jena.de/~nez/rechnerarithmetik_5/folien/Rechnerarithmetik.2008.komplett.pdf) (NB. This reference incorrectly gives the MANIAC II's floating point base as 256, whereas it actually is 65536.)
5.  ^     Beebe, Nelson H. F. (2017-08-22). "Chapter H. Historical floating-point architectures". *The Mathematical-Function Computation Handbook - Programming Using the MathCW Portable Software Library* (1st ed.). Salt Lake City, UT, USA: [Springer International Publishing AG](https://en.wikipedia.org/wiki/Springer_International_Publishing_AG). p. 948. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-319-64110-2](https://doi.org/10.1007%2F978-3-319-64110-2). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-64109-6](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-64109-6). [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [2017947446](https://lccn.loc.gov/2017947446). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [30244721](https://api.semanticscholar.org/CorpusID:30244721).
6.  Savard, John J. G. (2018) \[2007\], ["The Decimal Floating-Point Standard"](http://www.quadibloc.com/comp/cp020302.htm), *quadibloc*, [archived](https://web.archive.org/web/20180703002322/http://www.quadibloc.com/comp/cp020302.htm) from the original on 2018-07-03, retrieved 2018-07-16
7.  Parkinson, Roger (2000-12-07). ["Chapter 2 - High resolution digital site survey systems - Chapter 2.1 - Digital field recording systems"](https://books.google.com/books?id=Ocip5vpLD4wC&pg=PA24). *High Resolution Site Surveys* (1st ed.). [CRC Press](https://en.wikipedia.org/wiki/CRC_Press). p. 24. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-20318604-6](https://en.wikipedia.org/wiki/Special:BookSources/978-0-20318604-6). Retrieved 2019-08-18. “\[…\] Systems such as the \[Digital Field System\] DFS IV and DFS V were quaternary floating-point systems and used gain steps of 12 dB. \[…\]” (256 pages)
8.  Lazarus, Roger B. (1957-01-30) \[1956-10-01\]. ["MANIAC II"](http://bitsavers.org/pdf/lanl/LA-2083_MANIAC_II_Oct56.pdf) (PDF). Los Alamos, NM, USA: Los Alamos Scientific Laboratory of the University of California. p. 14. LA-2083. [Archived](https://web.archive.org/web/20180807200914/http://bitsavers.org/pdf/lanl/LA-2083_MANIAC_II_Oct56.pdf) (PDF) from the original on 2018-08-07. Retrieved 2018-08-07. “\[…\] the Maniac's floating base, which is 2<sup>16</sup> = 65,536. \[…\] The Maniac's large base permits a considerable increase in the speed of floating point arithmetic. Although such a large base implies the possibility of as many as 15 lead zeros, the large word size of 48 bits guarantees adequate significance. \[…\]”
9.  Torres Quevedo, Leonardo. [Automática: Complemento de la Teoría de las Máquinas, (pdf)](https://quickclick.es/rop/pdf/publico/1914/1914_tomoI_2043_01.pdf), pp. 575–583, Revista de Obras Públicas, 19 November 1914.
10. Ronald T. Kneusel. *[Numbers and Computers](https://books.google.com/books?id=eq4ZDgAAQBAJ&dq=leonardo+torres+quevedo++electromechanical+machine+essays&pg=PA84),* Springer, pp. 84–85, 2017. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3319505084](https://en.wikipedia.org/wiki/Special:BookSources/978-3319505084)
11. , pp. 6, 11–13.
12. Randell, Brian. [Digital Computers, History of Origins, (pdf)](https://dl.acm.org/doi/pdf/10.5555/1074100.1074334), p. 545, Digital Computers: Origins, Encyclopedia of Computer Science, January 2003.
13. [Rojas, Raúl](https://en.wikipedia.org/wiki/Ra%C3%BAl_Rojas) (April–June 1997). ["Konrad Zuse's Legacy: The Architecture of the Z1 and Z3"](http://ed-thelen.org/comp-hist/Zuse_Z1_and_Z3.pdf) (PDF). *[IEEE Annals of the History of Computing](https://en.wikipedia.org/wiki/IEEE_Annals_of_the_History_of_Computing)*. **19** (2): 5–16. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/85.586067](https://doi.org/10.1109%2F85.586067). [Archived](https://web.archive.org/web/20220703082408/http://ed-thelen.org/comp-hist/Zuse_Z1_and_Z3.pdf) (PDF) from the original on 2022-07-03. Retrieved 2022-07-03. (12 pages)
14. [Rojas, Raúl](https://en.wikipedia.org/wiki/Ra%C3%BAl_Rojas) (2014-06-07). "The Z1: Architecture and Algorithms of Konrad Zuse's First Computer". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1406.1886](https://arxiv.org/abs/1406.1886) \[[cs.AR](https://arxiv.org/archive/cs.AR)\].
15. ^   [Kahan, William Morton](https://en.wikipedia.org/wiki/William_Morton_Kahan) (1997-07-15). ["The Baleful Effect of Computer Languages and Benchmarks upon Applied Mathematics, Physics and Chemistry. John von Neumann Lecture"](https://people.eecs.berkeley.edu/~wkahan/SIAMjvnl.pdf) (PDF). p. 3. [Archived](https://web.archive.org/web/20080905103125/http://www.cs.berkeley.edu/~wkahan/SIAMjvnl.pdf) (PDF) from the original on 2008-09-05.
16. [Randell, Brian](https://en.wikipedia.org/wiki/Brian_Randell), ed. (1982) \[1973\]. *The Origins of Digital Computers: Selected Papers* (3rd ed.). Berlin; New York: [Springer-Verlag](https://en.wikipedia.org/wiki/Springer-Verlag). p. 244. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-11319-5](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-11319-5).
17. [Severance, Charles](https://en.wikipedia.org/wiki/Charles_Severance_(computer_scientist) "Charles Severance (computer scientist)") (1998-02-20). ["An Interview with the Old Man of Floating-Point"](https://people.eecs.berkeley.edu/~wkahan/ieee754status/754story.html).
18. ^     Goldberg, David (March 1991). ["What Every Computer Scientist Should Know About Floating-Point Arithmetic"](https://doi.org/10.1145%2F103162.103163). *[ACM Computing Surveys](https://en.wikipedia.org/wiki/ACM_Computing_Surveys)*. **23** (1): 5–48. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/103162.103163](https://doi.org/10.1145%2F103162.103163). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [222008826](https://api.semanticscholar.org/CorpusID:222008826). (With the addendum "Differences Among IEEE 754 Implementations": [2](https://en.wikipedia.org/wiki/2)(https://web.archive.org/web/20171011072644/http://www.cse.msu.edu/~cse320/Documents/FloatingPoint.pdf), [3](https://en.wikipedia.org/wiki/3)(https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html))
19. *ISO/IEC 9899:1999 - Programming languages - C*. Iso.org. §F.2, note 307. “"Extended" is IEC 60559's double-extended data format. Extended refers to both the common 80-bit and quadruple 128-bit IEC 60559 formats.”
20. ["IEEE Floating-Point Representation"](https://learn.microsoft.com/en-us/cpp/build/ieee-floating-point-representation). 2021-08-03.
21. [Using the GNU Compiler Collection, i386 and x86-64 Options](https://gcc.gnu.org/onlinedocs/gcc/i386-and-x86-64-Options.html) [Archived](https://web.archive.org/web/20150116065447/http://gcc.gnu.org/onlinedocs/gcc/i386-and-x86-64-Options.html) 2015-01-16 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine).
22. ["long double (GCC specific) and __float128"](https://stackoverflow.com/questions/13516476). *StackOverflow*.
23. ["Procedure Call Standard for the ARM 64-bit Architecture (AArch64)"](http://infocenter.arm.com/help/topic/com.arm.doc.ihi0055b/IHI0055B_aapcs64.pdf) (PDF). 2013-05-22. [Archived](https://web.archive.org/web/20130731181404/http://infocenter.arm.com/help/topic/com.arm.doc.ihi0055b/IHI0055B_aapcs64.pdf) (PDF) from the original on 2013-07-31. Retrieved 2019-09-22.
24. ["ARM Compiler toolchain Compiler Reference, Version 5.03"](http://infocenter.arm.com/help/topic/com.arm.doc.dui0491i/DUI0491I_arm_compiler_reference.pdf) (PDF). 2013. Section 6.3 *Basic data types*. [Archived](https://web.archive.org/web/20150627210618/http://infocenter.arm.com/help/topic/com.arm.doc.dui0491i/DUI0491I_arm_compiler_reference.pdf) (PDF) from the original on 2015-06-27. Retrieved 2019-11-08.
25. [Kahan, William Morton](https://en.wikipedia.org/wiki/William_Morton_Kahan) (2004-11-20). ["On the Cost of Floating-Point Computation Without Extra-Precise Arithmetic"](https://people.eecs.berkeley.edu/~wkahan/Qdrtcs.pdf) (PDF). [Archived](https://web.archive.org/web/20060525111157/http://www.cs.berkeley.edu/~wkahan/Qdrtcs.pdf) (PDF) from the original on 2006-05-25. Retrieved 2012-02-19.
26. ["openEXR"](https://web.archive.org/web/20130508221152/http://www.openexr.com/about.html). openEXR. Archived from [the original](http://www.openexr.com/about.html) on 2013-05-08. Retrieved 2012-04-25. “Since the IEEE-754 floating-point specification does not define a 16-bit format, ILM created the "half" format. Half values have 1 sign bit, 5 exponent bits, and 10 mantissa bits.”
27. ["Technical Introduction to OpenEXR – The half Data Type"](https://openexr.com/en/latest/TechnicalIntroduction.html#the-half-data-type). openEXR. Retrieved 2024-04-16.
28. ["IEEE-754 Analysis"](https://christophervickery.com/IEEE-754/). Retrieved 2024-08-29.
29. ^   Borland staff (1998-07-02) \[1994-03-10\]. ["Converting between Microsoft Binary and IEEE formats"](https://community.embarcadero.com/index.php/article/technical-articles/162-programming/14799-converting-between-microsoft-binary-and-ieee-forma). *Technical Information Database* (TI1431C.txt). [Embarcadero USA](https://en.wikipedia.org/wiki/Embarcadero_USA) / [Inprise](https://en.wikipedia.org/wiki/Inprise) (originally: [Borland](https://en.wikipedia.org/wiki/Borland)). ID 1400. [Archived](https://web.archive.org/web/20190220230417/https://community.embarcadero.com/index.php/article/technical-articles/162-programming/14799-converting-between-microsoft-binary-and-ieee-forma) from the original on 2019-02-20. Retrieved 2016-05-30. “\[…\] \_fmsbintoieee(float \*src4, float \*dest4) \[…\] MS Binary Format \[…\] byte order =\> m3 \| m2 \| m1 \| exponent \[…\] m1 is [most significant byte](https://en.wikipedia.org/wiki/Most_significant_byte) =\> sbbb\|bbbb \[…\] m3 is the [least significant byte](https://en.wikipedia.org/wiki/Least_significant_byte) \[…\] m = mantissa byte \[…\] s = sign bit \[…\] b = bit \[…\] MBF is bias 128 and IEEE is bias 127. \[…\] MBF places the [decimal point](https://en.wikipedia.org/wiki/Decimal_point) before the [assumed bit](https://en.wikipedia.org/wiki/Assumed_bit), while IEEE places the decimal point after the assumed bit. \[…\] ieee_exp = msbin\[3\] - 2; /\* actually, msbin\[3\]-1-128+127 \*/ \[…\] \_dmsbintoieee(double \*src8, double \*dest8) \[…\] MS Binary Format \[…\] byte order =\> m7 \| m6 \| m5 \| m4 \| m3 \| m2 \| m1 \| exponent \[…\] m1 is most significant byte =\> smmm\|mmmm \[…\] m7 is the least significant byte \[…\] MBF is bias 128 and IEEE is bias 1023. \[…\] MBF places the decimal point before the assumed bit, while IEEE places the decimal point after the assumed bit. \[…\] ieee_exp = msbin\[7\] - 128 - 1 + 1023; \[…\]”
30. ^   Steil, Michael (2008-10-20). ["Create your own Version of Microsoft BASIC for 6502"](http://www.pagetable.com/?p=46). pagetable.com. [Archived](https://web.archive.org/web/20160530092603/http://www.pagetable.com/?p=46) from the original on 2016-05-30. Retrieved 2016-05-30.
31. ["IEEE vs. Microsoft Binary Format; Rounding Issues (Complete)"](https://www.betaarchive.com/wiki/index.php/Microsoft_KB_Archive/35826#IEEE_vs._Microsoft_Binary_Format.3B_Rounding_Issues_.28Complete.29). *Microsoft Support*. [Microsoft](https://en.wikipedia.org/wiki/Microsoft). 2006-11-21. Article ID KB35826, Q35826. [Archived](https://web.archive.org/web/20200828130651/https://www.betaarchive.com/wiki/index.php/Microsoft_KB_Archive/35826) from the original on 2020-08-28. Retrieved 2010-02-24.
32. ^   Kharya, Paresh (2020-05-14). ["TensorFloat-32 in the A100 GPU Accelerates AI Training, HPC up to 20x"](https://blogs.nvidia.com/blog/2020/05/14/tensorfloat-32-precision-format/). Retrieved 2020-05-16.
33. ["NVIDIA Hopper Architecture In-Depth"](https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth/). 2022-03-22.
34. Micikevicius, Paulius; Stosic, Dusan; Burgess, Neil; Cornea, Marius; Dubey, Pradeep; Grisenthwaite, Richard; Ha, Sangwon; Heinecke, Alexander; Judd, Patrick; Kamalu, John; Mellempudi, Naveen; Oberman, Stuart; Shoeybi, Mohammad; Siu, Michael; Wu, Hao (2022-09-12). "FP8 Formats for Deep Learning". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2209.05433](https://arxiv.org/abs/2209.05433) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
35. [Kahan, William Morton](https://en.wikipedia.org/wiki/William_Morton_Kahan) (2006-01-11). ["How Futile are Mindless Assessments of Roundoff in Floating-Point Computation?"](https://people.eecs.berkeley.edu/~wkahan/Mindless.pdf) (PDF). [Archived](https://web.archive.org/web/20041221020332/http://www.cs.berkeley.edu/~wkahan/Mindless.pdf) (PDF) from the original on 2004-12-21.
36. ^   Gay, David M. (1990). *Correctly Rounded Binary-Decimal and Decimal-Binary Conversions* (Technical report). NUMERICAL ANALYSIS MANUSCRIPT 90-10, AT&T BELL LABORATORIES. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.31.4049](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.31.4049). ([dtoa.c in netlab](http://www.netlib.org/fp/dtoa.c))
37. Loitsch, Florian (2010). ["Printing floating-point numbers quickly and accurately with integers"](https://www.cs.tufts.edu/~nr/cs257/archive/florian-loitsch/printf.pdf) (PDF). *Proceedings of the 31st ACM SIGPLAN Conference on Programming Language Design and Implementation*. PLDI '10: ACM SIGPLAN Conference on Programming Language Design and Implementation. pp. 233–243. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/1806596.1806623](https://doi.org/10.1145%2F1806596.1806623). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-45030019-3](https://en.wikipedia.org/wiki/Special:BookSources/978-1-45030019-3). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [910409](https://api.semanticscholar.org/CorpusID:910409). [Archived](https://web.archive.org/web/20140729005717/http://www.cs.tufts.edu/~nr/cs257/archive/florian-loitsch/printf.pdf) (PDF) from the original on 2014-07-29.
38. ["Added Grisu3 algorithm support for double.ToString(). by mazong1123 · Pull Request #14646 · dotnet/coreclr"](https://github.com/dotnet/coreclr/pull/14646). *GitHub*.
39. Adams, Ulf (2018-12-02). ["Ryū: fast float-to-string conversion"](https://doi.org/10.1145%2F3296979.3192369). *ACM SIGPLAN Notices*. **53** (4): 270–282. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/3296979.3192369](https://doi.org/10.1145%2F3296979.3192369). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [218472153](https://api.semanticscholar.org/CorpusID:218472153).
40. Giulietti, Rafaello. ["The Schubfach way to render doubles"](https://drive.google.com/file/d/1IEeATSVnEE6TkrHlCYNY2GjaraBjOT4f).
41. ["abolz/Drachennest"](https://github.com/abolz/Drachennest). *[GitHub](https://en.wikipedia.org/wiki/GitHub)*. 2022-11-10.
42. ["google/double-conversion"](https://github.com/google/double-conversion). *[GitHub](https://en.wikipedia.org/wiki/GitHub)*. 2020-09-21.
43. Lemire, Daniel (2021-03-22). "Number parsing at a gigabyte per second". *Software: Practice and Experience*. **51** (8): 1700–1727. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[2101.11408](https://arxiv.org/abs/2101.11408). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/spe.2984](https://doi.org/10.1002%2Fspe.2984). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [231718830](https://api.semanticscholar.org/CorpusID:231718830).
44. Patterson, David A.; Hennessy, John L. (2014). *Computer Organization and Design, The Hardware/Software Interface*. The Morgan Kaufmann series in computer architecture and design (5th ed.). Waltham, Massachusetts, USA: Elsevier. p. 793. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-9-86605267-5](https://en.wikipedia.org/wiki/Special:BookSources/978-9-86605267-5).
45. ^   [US patent 3037701A](https://worldwide.espacenet.com/textdoc?DB=EPODOC&IDX=US3037701A), Huberto M Sierra, "Floating decimal point arithmetic control means for calculator", issued 1962-06-05 
46. ^   [Kahan, William Morton](https://en.wikipedia.org/wiki/William_Morton_Kahan) (1997-10-01). ["Lecture Notes on the Status of IEEE Standard 754 for Binary Floating-Point Arithmetic"](https://people.eecs.berkeley.edu/~wkahan/ieee754status/IEEE754.PDF) (PDF). p. 9. [Archived](https://web.archive.org/web/20020622093102/http://www.cs.berkeley.edu/~wkahan/ieee754status/IEEE754.PDF) (PDF) from the original on 2002-06-22.
47. ["D.3.2.1"](http://www.intel.com/content/www/us/en/processors/architectures-software-developer-manuals.html). *Intel 64 and IA-32 Architectures Software Developers' Manuals*. Vol. 1.
48. Harris, Richard (October 2010). ["You're Going To Have To Think!"](http://accu.org/index.php/journals/1702). *[Overload](https://en.wikipedia.org/wiki/Overload_(magazine) "Overload (magazine)")* (99): 5–10. [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1354-3172](https://search.worldcat.org/issn/1354-3172). Retrieved 2011-09-24. “Far more worrying is cancellation error which can yield catastrophic loss of precision.” [4](https://en.wikipedia.org/wiki/4)(http://accu.org/var/uploads/journals/overload99.pdf)
49. Christopher Barker: [PEP 485 -- A Function for testing approximate equality](https://www.python.org/dev/peps/pep-0485/)
50. ^   ["Patriot missile defense, Software problem led to system failure at Dharhan, Saudi Arabia"](http://www.gao.gov/products/IMTEC-92-26). [US Government Accounting Office](https://en.wikipedia.org/wiki/US_Government_Accounting_Office). GAO report IMTEC 92-26.
51. ^   Skeel, Robert (July 1992), ["Roundoff Error and the Patriot Missile"](https://www-users.cse.umn.edu/~arnold/disasters/Patriot-dharan-skeel-siam.pdf) (PDF), *SIAM News*, **25** (4): 11, retrieved 2024-11-15
52. [Wilkinson, James Hardy](https://en.wikipedia.org/wiki/James_Hardy_Wilkinson) (2003-09-08). "Error Analysis". In Ralston, Anthony; Reilly, Edwin D.; Hemmendinger, David (eds.). [Encyclopedia of Computer Science](https://books.google.com/books?id=OLRwQgAACAAJ). [Wiley](https://en.wikipedia.org/wiki/Wiley_(publisher) "Wiley (publisher)"). pp. 669–674. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-470-86412-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-470-86412-8). Retrieved 2013-05-14.
53. Einarsson, Bo (2005). [Accuracy and reliability in scientific computing](https://books.google.com/books?id=sh4orx_qB_QC&pg=PA50). [Society for Industrial and Applied Mathematics](https://en.wikipedia.org/wiki/Society_for_Industrial_and_Applied_Mathematics) (SIAM). pp. 50–. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-815-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-815-7). Retrieved 2013-05-14.
54. ^     [Higham, Nicholas John](https://en.wikipedia.org/wiki/Nicholas_Higham) (2002). [Accuracy and Stability of Numerical Algorithms](https://books.google.com/books?id=epilvM5MMxwC) (2nd ed.). [Society for Industrial and Applied Mathematics](https://en.wikipedia.org/wiki/Society_for_Industrial_and_Applied_Mathematics) (SIAM). pp. 27–28, 110–123, 493. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-89871-521-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-89871-521-7). 0-89871-355-2.
55. Oliveira, Suely; Stewart, David E. (2006-09-07). [Writing Scientific Software: A Guide to Good Style](https://books.google.com/books?id=E6a8oZOS8noC&pg=PA10). [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). pp. 10–. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-139-45862-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-139-45862-7).
56. ^   [Kahan, William Morton](https://en.wikipedia.org/wiki/William_Morton_Kahan) (2005-07-15). [Floating-Point Arithmetic Besieged by "Business Decisions"](https://people.eecs.berkeley.edu/~wkahan/ARITH_17.pdf) (PDF). IEEE-sponsored [ARITH 17](https://en.wikipedia.org/wiki/ARITH_17), Symposium on Computer Arithmetic (Keynote Address). pp. 6, 18. [Archived](https://web.archive.org/web/20060317103619/http://www.cs.berkeley.edu/~wkahan/ARITH_17.pdf) (PDF) from the original on 2006-03-17. Retrieved 2013-05-23. (NB. Kahan estimates that the incidence of excessively inaccurate results near singularities is reduced by a factor of approx. 1/2000 using the 11 extra bits of precision of [double extended](https://en.wikipedia.org/wiki/Extended_precision).)
57. [Kahan, William Morton](https://en.wikipedia.org/wiki/William_Morton_Kahan) (2011-08-03). [Desperately Needed Remedies for the Undebuggability of Large Floating-Point Computations in Science and Engineering](https://people.eecs.berkeley.edu/~wkahan/Boulder.pdf) (PDF). IFIP/SIAM/NIST Working Conference on Uncertainty Quantification in Scientific Computing, Boulder, CO. p. 33. [Archived](https://web.archive.org/web/20130620140729/http://www.eecs.berkeley.edu/~wkahan/Boulder.pdf) (PDF) from the original on 2013-06-20.
58. ^   [Kahan, William Morton](https://en.wikipedia.org/wiki/William_Morton_Kahan); Darcy, Joseph (2001) \[1998-03-01\]. ["How Java's floating-point hurts everyone everywhere"](https://people.eecs.berkeley.edu/~wkahan/JAVAhurt.pdf) (PDF). [Archived](https://web.archive.org/web/20000816043653/http://www.cs.berkeley.edu/~wkahan/JAVAhurt.pdf) (PDF) from the original on 2000-08-16. Retrieved 2003-09-05.
59. ^     [Kahan, William Morton](https://en.wikipedia.org/wiki/William_Morton_Kahan) (2000-08-27). ["Marketing versus Mathematics"](https://people.eecs.berkeley.edu/~wkahan/MktgMath.pdf) (PDF). pp. 15, 35, 47. [Archived](https://web.archive.org/web/20030815150333/http://www.cs.berkeley.edu/~wkahan/MktgMath.pdf) (PDF) from the original on 2003-08-15.
60. [Kahan, William Morton](https://en.wikipedia.org/wiki/William_Morton_Kahan) (1981-02-12). ["Why do we need a floating-point arithmetic standard?"](https://people.eecs.berkeley.edu/~wkahan/ieee754status/why-ieee.pdf) (PDF). p. 26. [Archived](https://web.archive.org/web/20041204070746/http://www.cs.berkeley.edu/~wkahan/ieee754status/why-ieee.pdf) (PDF) from the original on 2004-12-04.
61. [Kahan, William Morton](https://en.wikipedia.org/wiki/William_Morton_Kahan) (2001-06-04). Bindel, David (ed.). ["Lecture notes of System Support for Scientific Computation"](http://www.cims.nyu.edu/~dbindel/class/cs279/notes-06-04.pdf) (PDF). [Archived](https://web.archive.org/web/20130517181356/http://www.cims.nyu.edu/~dbindel/class/cs279/notes-06-04.pdf) (PDF) from the original on 2013-05-17.
62. ["General Decimal Arithmetic"](https://speleotrove.com/decimal/). Speleotrove.com. Retrieved 2012-04-25.
63. Christiansen, Tom; Torkington, Nathan; et al. (2006). ["perlfaq4 / Why is int() broken?"](https://perldoc.perl.org/5.8.8/perlfaq4#Why-is-int()-broken?). perldoc.perl.org. Retrieved 2011-01-11.
64. Shewchuk, Jonathan Richard (1997). ["Adaptive Precision Floating-Point Arithmetic and Fast Robust Geometric Predicates"](https://doi.org/10.1007%2FPL00009321). *[Discrete & Computational Geometry](https://en.wikipedia.org/wiki/Discrete_%26_Computational_Geometry)*. **18** (3): 305–363. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/PL00009321](https://doi.org/10.1007%2FPL00009321).
65. [Kahan, William Morton](https://en.wikipedia.org/wiki/William_Morton_Kahan); Ivory, Melody Y. (1997-07-03). ["Roundoff Degrades an Idealized Cantilever"](https://people.eecs.berkeley.edu/~wkahan/Cantilever.pdf) (PDF). [Archived](https://web.archive.org/web/20031205191038/http://www.cs.berkeley.edu/~wkahan/Cantilever.pdf) (PDF) from the original on 2003-12-05.
66. ["Auto-Vectorization in LLVM"](https://llvm.org/docs/Vectorizers.html). *LLVM 13 documentation*. “We support floating point reduction operations when -ffast-math is used.”
67. Kaylor, Andy (October 2024). ["Towards Useful Fast-Math"](https://llvm.org/devmtg/2024-10/slides/techtalk/Kaylor-Towards-Useful-Fast-Math.pdf) (PDF).
68. ["FloatingPointMath"](https://gcc.gnu.org/wiki/FloatingPointMath). *GCC Wiki*.
69. ["55522 – -funsafe-math-optimizations is unexpectedly harmful, especially w/ -shared"](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=55522). *gcc.gnu.org*.
70. ["Code Gen Options (The GNU Fortran Compiler)"](https://gcc.gnu.org/onlinedocs/gfortran/Code-Gen-Options.html). *gcc.gnu.org*.
71. ["Bug in zheevd · Issue #43 · Reference-LAPACK/lapack"](https://github.com/Reference-LAPACK/lapack/issues/43). *GitHub*.
72. Becker, Heiko; Darulova, Eva; Myreen, Magnus O.; Tatlock, Zachary (2019). *Icing: Supporting Fast-Math Style Optimizations in a Verified Compiler*. CAV 2019: Computer Aided Verification. Vol. 11562. pp. 155–173. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-030-25543-5_10](https://doi.org/10.1007%2F978-3-030-25543-5_10).

## Further reading

- [Wilkinson, James Hardy](https://en.wikipedia.org/wiki/James_Hardy_Wilkinson) (1963). [Rounding Errors in Algebraic Processes](https://books.google.com/books?id=yFogU9Ot-qsC) (1st ed.). Englewood Cliffs, New Jersey, USA: [Prentice-Hall, Inc.](https://en.wikipedia.org/wiki/Prentice-Hall,_Inc.) [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780486679990](https://en.wikipedia.org/wiki/Special:BookSources/9780486679990). [MR](https://en.wikipedia.org/wiki/MR_(identifier)) [0161456](https://mathscinet.ams.org/mathscinet-getitem?mr=0161456). `{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: ISBN / Date incompatibility ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#invalid_isbn_date)) (NB. Classic influential treatises on floating-point arithmetic.)
- [Wilkinson, James Hardy](https://en.wikipedia.org/wiki/James_Hardy_Wilkinson) (1965). [The Algebraic Eigenvalue Problem](https://books.google.com/books?id=N98IAQAAIAAJ&q=editions:ISBN0198534183). Monographs on Numerical Analysis (1st ed.). [Oxford University Press](https://en.wikipedia.org/wiki/Oxford_University_Press) / [Clarendon Press](https://en.wikipedia.org/wiki/Clarendon_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780198534037](https://en.wikipedia.org/wiki/Special:BookSources/9780198534037). Retrieved 2016-02-11.
- Sterbenz, Pat H. (1974). *Floating-Point Computation*. Prentice-Hall Series in Automatic Computation (1st ed.). Englewood Cliffs, New Jersey, USA: [Prentice Hall](https://en.wikipedia.org/wiki/Prentice_Hall). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-13-322495-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-13-322495-5).
- Golub, Gene F.; van Loan, Charles F. (1986). *Matrix Computations* (3rd ed.). [Johns Hopkins University Press](https://en.wikipedia.org/wiki/Johns_Hopkins_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8018-5413-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8018-5413-2).
- [Press, William Henry](https://en.wikipedia.org/wiki/William_Henry_Press); [Teukolsky, Saul A.](https://en.wikipedia.org/wiki/Saul_A._Teukolsky); [Vetterling, William T.](https://en.wikipedia.org/wiki/William_T._Vetterling); [Flannery, Brian P.](https://en.wikipedia.org/wiki/Brian_P._Flannery) (2007) \[1986\]. [*Numerical Recipes - The Art of Scientific Computing*](https://en.wikipedia.org/wiki/Numerical_Recipes) (3rd ed.). [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-88407-5](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-88407-5). (NB. Edition with source code CD-ROM.)
- [Knuth, Donald Ervin](https://en.wikipedia.org/wiki/Donald_Ervin_Knuth) (1997). "Section 4.2: Floating-Point Arithmetic". *[The Art of Computer Programming](https://en.wikipedia.org/wiki/The_Art_of_Computer_Programming)*, Vol. 2: *Seminumerical Algorithms* (3rd ed.). [Addison-Wesley](https://en.wikipedia.org/wiki/Addison-Wesley). pp. 214–264. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-201-89684-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-201-89684-8).
- [Blaauw, Gerrit Anne](https://en.wikipedia.org/wiki/Gerrit_Anne_Blaauw); [Brooks, Jr., Frederick Phillips](https://en.wikipedia.org/wiki/Frederick_Phillips_Brooks,_Jr.) (1997). *Computer Architecture: Concepts and Evolution* (1st ed.). [Addison-Wesley](https://en.wikipedia.org/wiki/Addison-Wesley). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-201-10557-8](https://en.wikipedia.org/wiki/Special:BookSources/0-201-10557-8). (1213 pages) (NB. This is a single-volume edition. This work was also available in a two-volume version.)
- Kornerup, Peter; Matula, David W. (2010). *Finite Precision Number Systems and Arithmetic*. [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-76135-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-76135-2).
- Savard, John J. G. (2018) \[2005\], ["Floating-Point Formats"](http://www.quadibloc.com/comp/cp0201.htm), *quadibloc*, [archived](https://web.archive.org/web/20180703001709/http://www.quadibloc.com/comp/cp0201.htm) from the original on 2018-07-03, retrieved 2018-07-16
- Muller, Jean-Michel; Brunie, Nicolas; de Dinechin, Florent; Jeannerod, Claude-Pierre; Joldes, Mioara; Lefèvre, Vincent; Melquiond, Guillaume; [Revol, Nathalie](https://en.wikipedia.org/wiki/Nathalie_Revol); Torres, Serge (2018) \[2010\]. [Handbook of Floating-Point Arithmetic](https://books.google.com/books?id=h3ZZDwAAQBAJ) (2nd ed.). [Birkhäuser](https://en.wikipedia.org/wiki/Birkh%C3%A4user). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-319-76526-6](https://doi.org/10.1007%2F978-3-319-76526-6). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-319-76525-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-319-76525-9). [LCCN](https://en.wikipedia.org/wiki/LCCN_(identifier)) [2018935254](https://lccn.loc.gov/2018935254).

## External links

- ["Survey of Floating-Point Formats"](http://www.mrob.com/pub/math/floatformats.html). (NB. This page gives a very brief summary of floating-point formats that have been used over the years.)
- Monniaux, David (May 2008). ["The pitfalls of verifying floating-point computations"](https://hal.science/hal-00128124/en/). *ACM Transactions on Programming Languages and Systems*. **30** (3). [Association for Computing Machinery](https://en.wikipedia.org/wiki/Association_for_Computing_Machinery) (ACM) Transactions on programming languages and systems (TOPLAS): 1–41. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[cs/0701192](https://arxiv.org/abs/cs/0701192). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1145/1353445.1353446](https://doi.org/10.1145%2F1353445.1353446). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [218578808](https://api.semanticscholar.org/CorpusID:218578808). (NB. A compendium of non-intuitive behaviors of floating point on popular architectures, with implications for program verification and testing.)
- [OpenCores](https://opencores.org/). (NB. This website contains open source floating-point IP cores for the implementation of floating-point operators in FPGA or ASIC devices. The project *double_fpu* contains verilog source code of a double-precision floating-point unit. The project *fpuvhdl* contains vhdl source code of a single-precision floating-point unit.)
- Fleegal, Eric (2004). ["Microsoft Visual C++ Floating-Point Optimization"](https://web.archive.org/web/20170706020455/http://msdn.microsoft.com/en-us/library/aa289157(v=vs.71).aspx). [Microsoft Developer Network](https://en.wikipedia.org/wiki/Microsoft_Developer_Network). Archived from [the original](http://msdn.microsoft.com/en-us/library/aa289157(v=vs.71).aspx) on 2017-07-06.
