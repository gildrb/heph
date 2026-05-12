[[information-theory.base]]

> Source: [Coding theory](https://en.wikipedia.org/wiki/Coding_theory)
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/1eba338d7d21e9227aa43feb3a933f27a26b1c5b.jpg]]
A two-dimensional visualisation of the [Hamming distance](https://en.wikipedia.org/wiki/Hamming_distance), a critical measure in coding theory

**Coding theory** is the study of the properties of [[code|codes]] and their respective fitness for specific applications. Codes are used for [data compression](https://en.wikipedia.org/wiki/Data_compression), [cryptography](https://en.wikipedia.org/wiki/Cryptography), [error detection and correction](https://en.wikipedia.org/wiki/Error_detection_and_correction), [data transmission](https://en.wikipedia.org/wiki/Data_transmission) and [data storage](https://en.wikipedia.org/wiki/Computer_data_storage). Codes are studied by various scientific disciplines—such as [information theory](https://en.wikipedia.org/wiki/Information_theory), [electrical engineering](https://en.wikipedia.org/wiki/Electrical_engineering), [mathematics](https://en.wikipedia.org/wiki/Mathematics), [linguistics](https://en.wikipedia.org/wiki/Linguistics), and [computer science](https://en.wikipedia.org/wiki/Computer_science)—for the purpose of designing efficient and reliable [data transmission](https://en.wikipedia.org/wiki/Data_transmission) methods. This typically involves the removal of redundancy and the correction or detection of errors in the transmitted data.

There are four types of coding:

1.  [Data compression](https://en.wikipedia.org/wiki/Data_compression) (or *source coding*)
2.  [Error control](https://en.wikipedia.org/wiki/Error_detection_and_correction) (or *channel coding*)
3.  [Cryptographic coding](https://en.wikipedia.org/wiki/Cryptography)
4.  [Line coding](https://en.wikipedia.org/wiki/Line_code)

Data compression attempts to remove unwanted redundancy from the data from a source in order to transmit it more efficiently. For example, [DEFLATE](https://en.wikipedia.org/wiki/DEFLATE) data compression makes files smaller, for purposes such as to reduce Internet traffic. Data compression and error correction may be [studied in combination](https://en.wikipedia.org/wiki/Joint_source_and_channel_coding).

Error correction adds useful [redundancy](https://en.wikipedia.org/wiki/Redundancy_(information_theory) "Redundancy (information theory)") to the data from a source to make the transmission more robust to disturbances present on the transmission channel. The ordinary user may not be aware of many applications using error correction. A typical [music compact disc](https://en.wikipedia.org/wiki/Compact_Disc_Digital_Audio) (CD) uses the [Reed–Solomon code](https://en.wikipedia.org/wiki/Reed%E2%80%93Solomon_code) to correct for scratches and dust. In this application the transmission channel is the CD itself. Cell phones also use coding techniques to correct for the [fading](https://en.wikipedia.org/wiki/Fading) and noise of high frequency radio transmission. Data modems, telephone transmissions, and the [NASA Deep Space Network](https://en.wikipedia.org/wiki/NASA_Deep_Space_Network) all employ channel coding techniques to get the bits through, for example the [turbo code](https://en.wikipedia.org/wiki/Turbo_code) and [LDPC codes](https://en.wikipedia.org/wiki/LDPC_code).

## History of coding theory

The decisive event which established the discipline of [information theory](https://en.wikipedia.org/wiki/Information_theory), and brought it to immediate worldwide attention, was the publication of [Claude E. Shannon](https://en.wikipedia.org/wiki/Claude_E._Shannon)'s classic paper "[A Mathematical Theory of Communication](https://en.wikipedia.org/wiki/A_Mathematical_Theory_of_Communication)" in the *[Bell System Technical Journal](https://en.wikipedia.org/wiki/Bell_System_Technical_Journal)* in July and October 1948.

In this revolutionary and groundbreaking paper, the work for which Shannon had substantially completed at Bell Labs by the end of 1944, Shannon for the first time introduced the qualitative and quantitative model of communication as a statistical process underlying information theory, opening with the assertion that

"The fundamental problem of communication is that of reproducing at one point, either exactly or approximately, a message selected at another point."

With it came the ideas of

- the [information entropy](https://en.wikipedia.org/wiki/Information_entropy) and [redundancy](https://en.wikipedia.org/wiki/Redundancy_(information_theory) "Redundancy (information theory)") of a source, and its relevance through the [source coding theorem](https://en.wikipedia.org/wiki/Shannon%27s_source_coding_theorem);
- the [[Mutual Information]], and the [channel capacity](https://en.wikipedia.org/wiki/Channel_capacity) of a noisy channel, including the promise of perfect loss-free communication given by the [noisy-channel coding theorem](https://en.wikipedia.org/wiki/Noisy-channel_coding_theorem);
- the practical result of the [Shannon–Hartley law](https://en.wikipedia.org/wiki/Shannon%E2%80%93Hartley_theorem) for the channel capacity of a Gaussian channel; and of course
- the [bit](https://en.wikipedia.org/wiki/Bit) - a new way of seeing the most fundamental unit of information.

Shannon’s paper focuses on the problem of how to best encode the [information](https://en.wikipedia.org/wiki/Information) a sender wants to transmit. In this fundamental work he used tools in probability theory, developed by [Norbert Wiener](https://en.wikipedia.org/wiki/Norbert_Wiener), which were in their nascent stages of being applied to communication theory at that time. Shannon developed [information entropy](https://en.wikipedia.org/wiki/Information_entropy) as a measure for the uncertainty in a message while essentially inventing the field of [information theory](https://en.wikipedia.org/wiki/Information_theory).

The [binary Golay code](https://en.wikipedia.org/wiki/Binary_Golay_code) was developed in 1949. It is an error-correcting code capable of correcting up to three errors in each 24-bit word, and detecting a fourth.

[Richard Hamming](https://en.wikipedia.org/wiki/Richard_Hamming) won the [Turing Award](https://en.wikipedia.org/wiki/Turing_Award) in 1968 for his work at [Bell Labs](https://en.wikipedia.org/wiki/Bell_Labs) in numerical methods, automatic coding systems, and error-detecting and error-correcting codes. He invented the concepts known as [Hamming codes](https://en.wikipedia.org/wiki/Hamming_code), [Hamming windows](https://en.wikipedia.org/wiki/Hamming_window), [Hamming numbers](https://en.wikipedia.org/wiki/Hamming_numbers), and [Hamming distance](https://en.wikipedia.org/wiki/Hamming_distance).

In 1972, [Nasir Ahmed](https://en.wikipedia.org/wiki/N._Ahmed) proposed the [discrete cosine transform](https://en.wikipedia.org/wiki/Discrete_cosine_transform) (DCT), which he developed with T. Natarajan and [K. R. Rao](https://en.wikipedia.org/wiki/K._R._Rao) in 1973. The DCT is the most widely used [lossy compression](https://en.wikipedia.org/wiki/Lossy_compression) algorithm, the basis for multimedia formats such as [JPEG](https://en.wikipedia.org/wiki/JPEG), [MPEG](https://en.wikipedia.org/wiki/MPEG) and [MP3](https://en.wikipedia.org/wiki/MP3).

## Source coding

The aim of source coding is to take the source data and make it smaller.

### Definition

Data can be seen as a [random variable](https://en.wikipedia.org/wiki/Random_variable) $X:\Omega \to {\mathcal {X}}$, where $x\in {\mathcal {X}}$ appears with probability $\mathbb {P} [X=x]$.

Data are encoded by strings (words) over an [alphabet](https://en.wikipedia.org/wiki/Alphabet_(computer_science)) $\Sigma$.

A code is a function

$C:{\mathcal {X}}\to \Sigma ^{*}$ (or $\Sigma ^{+}$ if the empty string is not part of the alphabet).

$C(x)$ is the code word associated with $x$.

Length of the code word is written as

$l(C(x)).$

Expected length of a code is

$l(C)=\sum _{x\in {\mathcal {X}}}l(C(x))\mathbb {P} [X=x].$

The concatenation of code words $C(x_{1},\ldots ,x_{k})=C(x_{1})C(x_{2})\cdots C(x_{k})$.

The code word of the empty string is the empty string itself:

$C(\epsilon )=\epsilon$

### Properties

1.  $C:{\mathcal {X}}\to \Sigma ^{*}$ is [non-singular](https://en.wikipedia.org/wiki/Variable-length_code#Non-singular_codes) if [injective](https://en.wikipedia.org/wiki/Injective_function).
2.  $C:{\mathcal {X}}^{*}\to \Sigma ^{*}$ is [uniquely decodable](https://en.wikipedia.org/wiki/Uniquely_decodable_code#Uniquely_decodable_codes) if injective.
3.  $C:{\mathcal {X}}\to \Sigma ^{*}$ is [instantaneous](https://en.wikipedia.org/wiki/Variable-length_code#Prefix_codes) if $C(x_{1})$ is not a proper prefix of $C(x_{2})$ (and vice versa).

### Principle

[Entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory) "Entropy (information theory)") of a source is the measure of information. Basically, source codes try to reduce the redundancy present in the source, and represent the source with fewer bits that carry more information.

Data compression which explicitly tries to minimize the average length of messages according to a particular assumed probability model is called [entropy encoding](https://en.wikipedia.org/wiki/Entropy_encoding).

Various techniques used by source coding schemes try to achieve the limit of entropy of the source. *C*(*x*) ≥ *H*(*x*), where *H*(*x*) is entropy of source (bitrate), and *C*(*x*) is the bitrate after compression. In particular, no source coding scheme can be better than the entropy of the source.

### Example

[Facsimile](https://en.wikipedia.org/wiki/FAX) transmission uses a simple [run length code](https://en.wikipedia.org/wiki/Run-length_encoding). Source coding removes all data superfluous to the need of the transmitter, decreasing the bandwidth required for transmission.

## Channel coding

The purpose of channel coding theory is to find codes which transmit quickly, contain many valid [code words](https://en.wikipedia.org/wiki/Code_word_(communication) "Code word (communication)") and can correct or at least [detect](https://en.wikipedia.org/wiki/Error_detection) many errors. While not mutually exclusive, performance in these areas is a trade-off. So, different codes are optimal for different applications. The needed properties of this code mainly depend on the probability of errors happening during transmission. In a typical CD, the impairment is mainly dust or scratches.

CDs use [cross-interleaved Reed–Solomon coding](https://en.wikipedia.org/wiki/Cross-interleaved_Reed%E2%80%93Solomon_coding) to spread the data out over the disk.

Although not a very good code, a simple repeat code can serve as an understandable example. Suppose we take a block of data bits (representing sound) and send it three times. At the receiver we will examine the three repetitions bit by bit and take a majority vote. The twist on this is that we do not merely send the bits in order. We interleave them. The block of data bits is first divided into 4 smaller blocks. Then we cycle through the block and send one bit from the first, then the second, etc. This is done three times to spread the data out over the surface of the disk. In the context of the simple repeat code, this may not appear effective. However, there are more powerful codes known which are very effective at correcting the "burst" error of a scratch or a dust spot when this interleaving technique is used.

Other codes are more appropriate for different applications. Deep space communications are limited by the [thermal noise](https://en.wikipedia.org/wiki/Thermal_noise) of the receiver which is more of a continuous nature than a bursty nature. Likewise, narrowband modems are limited by the noise, present in the telephone network and also modeled better as a continuous disturbance.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> Cell phones are subject to rapid [fading](https://en.wikipedia.org/wiki/Fading). The high frequencies used can cause rapid fading of the signal even if the receiver is moved a few inches. Again there are a class of channel codes that are designed to combat fading.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

### Linear codes

The term **algebraic coding theory** denotes the sub-field of coding theory where the properties of codes are expressed in algebraic terms and then further researched.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

Algebraic coding theory is basically divided into two major types of codes:<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

- Linear block codes
- Convolutional codes

It analyzes the following three properties of a code – mainly:<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

- Code word length
- Total number of valid code words
- The minimum [distance](https://en.wikipedia.org/wiki/Distance) between two valid code words, using mainly the [Hamming distance](https://en.wikipedia.org/wiki/Hamming_distance), sometimes also other distances like the [Lee distance](https://en.wikipedia.org/wiki/Lee_distance)

#### Linear block codes

Linear block codes have the property of [linearity](https://en.wikipedia.org/wiki/Linearity), i.e. the sum of any two codewords is also a code word, and they are applied to the source bits in blocks, hence the name linear block codes. There are block codes that are not linear, but it is difficult to prove that a code is a good one without this property.

Linear block codes are summarized by their symbol alphabets (e.g., binary or ternary) and parameters (*n*,*m*,*d<sub>min</sub>*) where

1.  n is the length of the codeword, in symbols,
2.  m is the number of source symbols that will be used for encoding at once,
3.  *d<sub>min</sub>* is the minimum hamming distance for the code.

There are many types of linear block codes, such as

1.  [Cyclic codes](https://en.wikipedia.org/wiki/Cyclic_code) (e.g., [Hamming codes](https://en.wikipedia.org/wiki/Hamming_code))
2.  [Repetition codes](https://en.wikipedia.org/wiki/Repetition_code)
3.  [Parity codes](https://en.wikipedia.org/wiki/Parity_bit)
4.  [Polynomial codes](https://en.wikipedia.org/wiki/Polynomial_code) (e.g., [BCH codes](https://en.wikipedia.org/wiki/BCH_code))
5.  [Reed–Solomon codes](https://en.wikipedia.org/wiki/Reed%E2%80%93Solomon_error_correction)
6.  [Algebraic geometric codes](https://en.wikipedia.org/wiki/Algebraic_geometric_code)
7.  [Reed–Muller codes](https://en.wikipedia.org/wiki/Reed%E2%80%93Muller_code)
8.  [Perfect codes](https://en.wikipedia.org/wiki/Hamming_bound)
9.  [Locally recoverable code](https://en.wikipedia.org/wiki/Locally_recoverable_code)

Block codes are tied to the [sphere packing](https://en.wikipedia.org/wiki/Sphere_packing) problem, which has received some attention over the years. In two dimensions, it is easy to visualize. Take a bunch of pennies flat on the table and push them together. The result is a hexagon pattern like a bee's nest. But block codes rely on more dimensions which cannot easily be visualized. The powerful (24,12) [Golay code](https://en.wikipedia.org/wiki/Binary_Golay_code) used in deep space communications uses 24 dimensions. If used as a binary code (which it usually is) the dimensions refer to the length of the codeword as defined above.

The theory of coding uses the *N*-dimensional sphere model. For example, how many pennies can be packed into a circle on a tabletop, or in 3 dimensions, how many marbles can be packed into a globe. Other considerations enter the choice of a code. For example, hexagon packing into the constraint of a rectangular box will leave empty space at the corners. As the dimensions get larger, the percentage of empty space grows smaller. But at certain dimensions, the packing uses all the space and these codes are the so-called "perfect" codes. The only nontrivial and useful perfect codes are the distance-3 Hamming codes with parameters satisfying (2<sup>*r*</sup> – 1, 2<sup>*r*</sup> – 1 – *r*, 3), and the \[23,12,7\] binary and \[11,6,5\] ternary Golay codes.

Another code property is the number of neighbors that a single codeword may have. Again, consider pennies as an example. First we pack the pennies in a rectangular grid. Each penny will have 4 near neighbors (and 4 at the corners which are farther away). In a hexagon, each penny will have 6 near neighbors. When we increase the dimensions, the number of near neighbors increases very rapidly. The result is the number of ways for noise to make the receiver choose a neighbor (hence an error) grows as well. This is a fundamental limitation of block codes, and indeed all codes. It may be harder to cause an error to a single neighbor, but the number of neighbors can be large enough so the total error probability actually suffers.

Properties of linear block codes are used in many applications. For example, the syndrome-coset uniqueness property of linear block codes is used in trellis shaping, one of the best-known [shaping codes](https://en.wikipedia.org/wiki/Shaping_codes).

#### Convolutional codes

The idea behind a convolutional code is to make every codeword symbol be the weighted sum of the various input message symbols. This is like [convolution](https://en.wikipedia.org/wiki/Convolution) used in [LTI](https://en.wikipedia.org/wiki/Linear_time_invariant) systems to find the output of a system, when you know the input and impulse response.

So we generally find the output of the system convolutional encoder, which is the convolution of the input bit, against the states of the convolution encoder, registers.

Fundamentally, convolutional codes do not offer more protection against noise than an equivalent block code. In many cases, they generally offer greater simplicity of implementation over a block code of equal power. The encoder is usually a simple circuit which has state memory and some feedback logic, normally [XOR gates](https://en.wikipedia.org/wiki/XOR_gate). The [decoder](https://en.wikipedia.org/wiki/Decoding_methods) can be implemented in software or firmware.

The [Viterbi algorithm](https://en.wikipedia.org/wiki/Viterbi_algorithm) is the optimum algorithm used to decode convolutional codes. There are simplifications to reduce the computational load. They rely on searching only the most likely paths. Although not optimum, they have generally been found to give good results in low noise environments.

Convolutional codes are used in voiceband modems (V.32, V.17, V.34) and in GSM mobile phones, as well as satellite and military communication devices.

## Cryptographic coding

[Cryptography](https://en.wikipedia.org/wiki/Cryptography) or cryptographic coding is the practice and study of techniques for [secure communication](https://en.wikipedia.org/wiki/Secure_communication) in the presence of third parties (called [adversaries](https://en.wikipedia.org/wiki/Adversary_(cryptography) "Adversary (cryptography)")). More generally, it is about constructing and analyzing [protocols](https://en.wikipedia.org/wiki/Communications_protocol) that block adversaries; various aspects in [information security](https://en.wikipedia.org/wiki/Information_security) such as data [confidentiality](https://en.wikipedia.org/wiki/Confidentiality), [data integrity](https://en.wikipedia.org/wiki/Data_integrity), [authentication](https://en.wikipedia.org/wiki/Authentication), and [non-repudiation](https://en.wikipedia.org/wiki/Non-repudiation) are central to modern cryptography. Modern cryptography exists at the intersection of the disciplines of [mathematics](https://en.wikipedia.org/wiki/Mathematics), [computer science](https://en.wikipedia.org/wiki/Computer_science), and [electrical engineering](https://en.wikipedia.org/wiki/Electrical_engineering). Applications of cryptography include [ATM cards](https://en.wikipedia.org/wiki/Automated_teller_machine), [computer passwords](https://en.wikipedia.org/wiki/Password), and [electronic commerce](https://en.wikipedia.org/wiki/Electronic_commerce).

Cryptography prior to the modern age was effectively synonymous with *[encryption](https://en.wikipedia.org/wiki/Encryption)*, the conversion of information from a readable state to apparent [nonsense](https://en.wikipedia.org/wiki/Nonsense). The originator of an encrypted message shared the decoding technique needed to recover the original information only with intended recipients, thereby precluding unwanted persons from doing the same. Since [World War I](https://en.wikipedia.org/wiki/World_War_I) and the advent of the [computer](https://en.wikipedia.org/wiki/Computer), the methods used to carry out cryptology have become increasingly complex and its application more widespread.

Modern cryptography is heavily based on mathematical theory and computer science practice; cryptographic algorithms are designed around [computational hardness assumptions](https://en.wikipedia.org/wiki/Computational_hardness_assumption), making such algorithms hard to break in practice by any adversary. It is theoretically possible to break such a system, but it is infeasible to do so by any known practical means. These schemes are therefore termed computationally secure; theoretical advances, e.g., improvements in [integer factorization](https://en.wikipedia.org/wiki/Integer_factorization) algorithms, and faster computing technology require these solutions to be continually adapted. There exist [information-theoretically secure](https://en.wikipedia.org/wiki/Information_theoretic_security) schemes that provably cannot be broken even with unlimited computing power—an example is the [one-time pad](https://en.wikipedia.org/wiki/One-time_pad)—but these schemes are more difficult to implement than the best theoretically breakable but computationally secure mechanisms.

## Line coding

A [line code](https://en.wikipedia.org/wiki/Line_code) (also called digital baseband modulation or digital [baseband](https://en.wikipedia.org/wiki/Baseband) transmission method) is a [[code]] chosen for use within a [communications system](https://en.wikipedia.org/wiki/Communications_system) for baseband [transmission](https://en.wikipedia.org/wiki/Transmission_(telecommunications)) purposes.

Line coding is often used for digital data transport. It consists of representing the [digital signal](https://en.wikipedia.org/wiki/Digital_signal_(electronics)) to be transported by an amplitude- and time-discrete signal that is optimally tuned for the specific properties of the physical channel (and of the receiving equipment). The [waveform](https://en.wikipedia.org/wiki/Waveform) pattern of voltage or current used to represent the 1s and 0s of a digital data on a transmission link is called *line encoding*. The common types of line encoding are [unipolar](https://en.wikipedia.org/wiki/Unipolar_encoding), [polar](https://en.wikipedia.org/wiki/Polar_encoding), [bipolar](https://en.wikipedia.org/wiki/Bipolar_encoding), and [Manchester encoding](https://en.wikipedia.org/wiki/Manchester_encoding).

## Other applications of coding theory

Another concern of coding theory is designing codes that help [synchronization](https://en.wikipedia.org/wiki/Synchronization). A code may be designed so that a [phase shift](https://en.wikipedia.org/wiki/Phase_(waves) "Phase (waves)") can be easily detected and corrected and that multiple signals can be sent on the same channel.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

Another application of codes, used in some mobile phone systems, is [code-division multiple access](https://en.wikipedia.org/wiki/Code-division_multiple_access) (CDMA). Each phone is assigned a code sequence that is approximately uncorrelated with the codes of other phones.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> When transmitting, the code word is used to modulate the data bits representing the voice message. At the receiver, a demodulation process is performed to recover the data. The properties of this class of codes allow many users (with different codes) to use the same radio channel at the same time. To the receiver, the signals of other users will appear to the demodulator only as a low-level noise.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

Another general class of codes are the [automatic repeat-request](https://en.wikipedia.org/wiki/Automatic_repeat-request) (ARQ) codes. In these codes the sender adds redundancy to each message for error checking, usually by adding check bits. If the check bits are not consistent with the rest of the message when it arrives, the receiver will ask the sender to retransmit the message. All but the simplest [wide area network](https://en.wikipedia.org/wiki/Wide_area_network) protocols use ARQ. Common protocols include [SDLC](https://en.wikipedia.org/wiki/Synchronous_Data_Link_Control) (IBM), [TCP](https://en.wikipedia.org/wiki/Transmission_Control_Protocol) (Internet), [X.25](https://en.wikipedia.org/wiki/X.25) (International) and many others. There is an extensive field of research on this topic because of the problem of matching a rejected packet against a new packet. Is it a new one or is it a retransmission? Typically numbering schemes are used, as in TCP.["RFC793"](http://tools.ietf.org/html/rfc793). *RFCS*. [Internet Engineering Task Force](https://en.wikipedia.org/wiki/Internet_Engineering_Task_Force) (IETF). September 1981.

### Group testing

[Group testing](https://en.wikipedia.org/wiki/Group_testing) uses codes in a different way. Consider a large group of items in which a very few are different in a particular way (e.g., defective products or infected test subjects). The idea of group testing is to determine which items are "different" by using as few tests as possible. The origin of the problem has its roots in the [Second World War](https://en.wikipedia.org/wiki/Second_World_War) when the [United States Army Air Forces](https://en.wikipedia.org/wiki/United_States_Army_Air_Forces) needed to test its soldiers for [syphilis](https://en.wikipedia.org/wiki/Syphilis).

### Analog coding

Information is encoded analogously in the [neural networks](https://en.wikipedia.org/wiki/Neural_network) of [brains](https://en.wikipedia.org/wiki/Brain), in [analog signal processing](https://en.wikipedia.org/wiki/Analog_signal_processing), and [analog electronics](https://en.wikipedia.org/wiki/Analog_electronics). Aspects of analog coding include analog error correction, analog data compression and analog encryption.

## Neural coding

[Neural coding](https://en.wikipedia.org/wiki/Neural_coding) is a [neuroscience](https://en.wikipedia.org/wiki/Neuroscience)-related field concerned with how sensory and other information is represented in the [brain](https://en.wikipedia.org/wiki/Brain) by [networks](https://en.wikipedia.org/wiki/Neural_network) of [neurons](https://en.wikipedia.org/wiki/Neurons). The main goal of studying neural coding is to characterize the relationship between the [stimulus](https://en.wikipedia.org/wiki/Stimulus_(physiology) "Stimulus (physiology)") and the individual or ensemble neuronal responses and the relationship among electrical activity of the neurons in the ensemble. It is thought that neurons can encode both [digital](https://en.wikipedia.org/wiki/Digital_data) and [analog](https://en.wikipedia.org/wiki/Analog_signal) information, and that neurons follow the principles of information theory and compress information, and detect and correct errors in the signals that are sent throughout the brain and wider nervous system.

## See also

- ![[media/cad93a86f01aadbdcddeb94c9f1e22884f470b4f.png]][Telecommunication portal](https://en.wikipedia.org/wiki/Portal:Telecommunication)

- [Coding gain](https://en.wikipedia.org/wiki/Coding_gain)
- [Covering code](https://en.wikipedia.org/wiki/Covering_code)
- [Error correction code](https://en.wikipedia.org/wiki/Error_correction_code)
- [Folded Reed–Solomon code](https://en.wikipedia.org/wiki/Folded_Reed%E2%80%93Solomon_code)
- [Group testing](https://en.wikipedia.org/wiki/Group_testing)
- [Hamming distance](https://en.wikipedia.org/wiki/Hamming_distance), [Hamming weight](https://en.wikipedia.org/wiki/Hamming_weight)
- [Lee distance](https://en.wikipedia.org/wiki/Lee_distance)
- [List of algebraic coding theory topics](https://en.wikipedia.org/wiki/List_of_algebraic_coding_theory_topics)
- Spatial coding and [MIMO](https://en.wikipedia.org/wiki/MIMO) in multiple antenna research
  - [Spatial diversity coding](https://en.wikipedia.org/wiki/Space%E2%80%93time_code) is spatial coding that transmits replicas of the information signal along different spatial paths, so as to increase the reliability of the data transmission.
  - [Spatial interference cancellation coding](https://en.wikipedia.org/wiki/Dirty_paper_coding_(DPC))
  - [Spatial multiplex coding](https://en.wikipedia.org/wiki/Spatial_multiplexing)
- [Timeline of information theory, data compression, and error correcting codes](https://en.wikipedia.org/wiki/Timeline_of_information_theory)

## Notes

1.  James Irvine; David Harle (2002). "2.4.4 Types of Coding". [Data Communications and Networks](https://books.google.com/books?id=ZigejECe4r0C). John Wiley & Sons. p. 18. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780471808725](https://en.wikipedia.org/wiki/Special:BookSources/9780471808725). “There are four types of coding”
2.  [Nasir Ahmed](https://en.wikipedia.org/wiki/N._Ahmed). ["How I Came Up With the Discrete Cosine Transform"](https://www.scribd.com/doc/52879771/DCT-History). Digital Signal Processing, Vol. 1, Iss. 1, 1991, pp. 4-5.
3.  Todd Campbell. ["Answer Geek: Error Correction Rule CDs"](https://abcnews.go.com/Technology/story?id=119305&page=1).
4.  ^    [Terras, Audrey](https://en.wikipedia.org/wiki/Audrey_Terras) (1999). [Fourier Analysis on Finite Groups and Applications](https://archive.org/details/fourieranalysiso0000terr). [Cambridge University Press](https://en.wikipedia.org/wiki/Cambridge_University_Press). p. [195](https://archive.org/details/fourieranalysiso0000terr/page/195). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-45718-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-45718-7).
5.  ^   [Blahut, Richard E.](https://en.wikipedia.org/wiki/Richard_E._Blahut) (2003). [Algebraic Codes for Data Transmission](https://books.google.com/books?id=n0XHMY58tL8C&pg=PA60). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-55374-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-55374-2).
6.  ^    Christian Schlegel; Lance Pérez (2004). [Trellis and turbo coding](https://books.google.com/books?id=9wRCjfGAaEcC&pg=PA73). Wiley-IEEE. p. 73. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-22755-7](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-22755-7).
7.  [Forney, G.D. Jr.](https://en.wikipedia.org/wiki/Dave_Forney) (March 1992). "Trellis shaping". *IEEE Transactions on Information Theory*. **38** (2 Pt 2): 281–300. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/18.119687](https://doi.org/10.1109%2F18.119687). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [37984132](https://api.semanticscholar.org/CorpusID:37984132).
8.  [Rivest, Ronald L.](https://en.wikipedia.org/wiki/Ron_Rivest) (1990). "Cryptology". In J. Van Leeuwen (ed.). *Handbook of Theoretical Computer Science*. Vol. 1. Elsevier.
9.  Bellare, Mihir; Rogaway, Phillip (21 September 2005). "Introduction". *Introduction to Modern Cryptography*. p. 10.
10. Menezes, A. J.; van Oorschot, P. C.; Vanstone, S. A. (1997). [Handbook of Applied Cryptography](https://archive.org/details/handbookofapplie0000mene). Taylor & Francis. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-8493-8523-0](https://en.wikipedia.org/wiki/Special:BookSources/978-0-8493-8523-0).
11. Dorfman, Robert (1943). ["The detection of defective members of large populations"](https://doi.org/10.1214%2Faoms%2F1177731363). *Annals of Mathematical Statistics*. **14** (4): 436–440. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1214/aoms/1177731363](https://doi.org/10.1214%2Faoms%2F1177731363).
12. Chen, Brian; Wornell, Gregory W. (July 1998). ["Analog Error-Correcting Codes Based on Chaotic Dynamical Systems"](http://webarchive.loc.gov/all/20010927045421/http://allegro.mit.edu/dspg/publications/journals/pdf/98chen.pdf) (PDF). *IEEE Transactions on Communications*. **46** (7): 881–890. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.30.4093](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.30.4093). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/26.701312](https://doi.org/10.1109%2F26.701312). Archived from [the original](http://allegro.mit.edu/dspg/publications/Journals/pdf/98Chen.pdf) (PDF) on 2001-09-27. Retrieved 2013-06-30.
13. Novak, Franc; Hvala, Bojan; Klavžar, Sandi (1999). "On Analog Signature Analysis". *Proceedings of the conference on Design, automation and test in Europe*. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.142.5853](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.142.5853). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-58113-121-6](https://en.wikipedia.org/wiki/Special:BookSources/1-58113-121-6).
14. Shujun Li; Chengqing Li; Kwok-Tung Lo; Guanrong Chen (April 2008). ["Cryptanalyzing an Encryption Scheme Based on Blind Source Separation"](http://epubs.surrey.ac.uk/532452/1/IEEETCASI2008.pdf) (PDF). *IEEE Transactions on Circuits and Systems I*. **55** (4): 1055–63. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[cs/0608024](https://arxiv.org/abs/cs/0608024). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TCSI.2008.916540](https://doi.org/10.1109%2FTCSI.2008.916540). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [2224947](https://api.semanticscholar.org/CorpusID:2224947).
15. Brown EN, Kass RE, Mitra PP (May 2004). ["Multiple neural spike train data analysis: state-of-the-art and future challenges"](http://www.stat.columbia.edu/~liam//teaching/neurostat-fall13/papers/brown-et-al/brown-kass-mitra.pdf) (PDF). *Nature Neuroscience*. **7** (5): 456–461. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1038/nn1228](https://doi.org/10.1038%2Fnn1228). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [15114358](https://pubmed.ncbi.nlm.nih.gov/15114358). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [562815](https://api.semanticscholar.org/CorpusID:562815).
16. Thorpe, S.J. (1990). ["Spike arrival times: A highly efficient coding scheme for neural networks"](http://pop.cerco.ups-tlse.fr/fr_vers/documents/thorpe_sj_90_91.pdf) (PDF). In Eckmiller, R.; Hartmann, G.; [Hauske, G.](https://en.wikipedia.org/wiki/Gert_Hauske) (eds.). [Parallel processing in neural systems and computers](https://books.google.com/books?id=b9gmAAAAMAAJ) (PDF). North-Holland. pp. 91–94. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-444-88390-2](https://en.wikipedia.org/wiki/Special:BookSources/978-0-444-88390-2). Retrieved 30 June 2013.
17. Gedeon, T.; Parker, A.E.; Dimitrov, A.G. (Spring 2002). ["Information Distortion and Neural Coding"](https://web.archive.org/web/20161117220131/http://www.math.ualberta.ca/ami/CAMQ/table_of_content/vol_10/10_1c.htm). *Canadian Applied Mathematics Quarterly*. **10** (1): 10. [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.5.6365](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.5.6365). Archived from [the original](http://www.math.ualberta.ca/ami/CAMQ/table_of_content/vol_10/10_1c.htm) on 2016-11-17. Retrieved 2013-06-30.
18. Stiber, M. (July 2005). "Spike timing precision and neural error correction: local behavior". *Neural Computation*. **17** (7): 1577–1601. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[q-bio/0501021](https://arxiv.org/abs/q-bio/0501021). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1162/0899766053723069](https://doi.org/10.1162%2F0899766053723069). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [15901408](https://pubmed.ncbi.nlm.nih.gov/15901408). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [2064645](https://api.semanticscholar.org/CorpusID:2064645).

## References

- [Elwyn R. Berlekamp](https://en.wikipedia.org/wiki/Elwyn_R._Berlekamp) (2014), *Algebraic Coding Theory*, World Scientific Publishing (revised edition), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-9-81463-589-9](https://en.wikipedia.org/wiki/Special:BookSources/978-9-81463-589-9).
- [MacKay, David J. C.](https://en.wikipedia.org/wiki/David_J._C._MacKay) *[Information Theory, Inference, and Learning Algorithms](https://web.archive.org/web/20160217105359/http://www.inference.phy.cam.ac.uk/mackay/itila/book.html)* Cambridge: Cambridge University Press, 2003. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-521-64298-1](https://en.wikipedia.org/wiki/Special:BookSources/0-521-64298-1)
- [Vera Pless](https://en.wikipedia.org/wiki/Vera_Pless) (1982), *[Introduction to the Theory of Error-Correcting Codes](https://en.wikipedia.org/wiki/Introduction_to_the_Theory_of_Error-Correcting_Codes)*, John Wiley & Sons, Inc., [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [0-471-08684-3](https://en.wikipedia.org/wiki/Special:BookSources/0-471-08684-3).
- Randy Yates, *[A Coding Theory Tutorial](https://web.archive.org/web/20110710143034/http://www.digitalsignallabs.com/tutorial.pdf)*.
