# Scientific notes

An input state cos(θ/2)|0⟩ + exp(iφ)sin(θ/2)|1⟩ occupies q0. Alice and Bob share q1 and q2 in the resource state (1−p)|Φ+⟩⟨Φ+| + pI/4. Alice applies CNOT(q0,q1), then H(q0), and measures both qubits. Bob uses the second received bit for X and the first for Z.

The engine sums the measurement branches and classical-error patterns with their probabilities. The selected-input fidelity is ⟨ψ|ρout|ψ⟩. The mean weights the six Pauli eigenstates equally. Alice’s arrow is a stored comparison reference. Bob’s sphere in the lab represents the unconditional output after averaging.

With corrections enabled, the balanced average is (1−p)(1+2r)/3 + p/2. Here r is the chance neither bit flips: (1−e)² for independent errors, and 1−e for perfectly linked errors. Without corrections the averaged output is maximally mixed and the fidelity is 1/2. The fair classical measure-and-prepare comparison for this ensemble is 2/3.

The sweep uses fixed e and ideal gates and measurements. Optical loss, timing, detectors and storage decoherence are outside this model. In particular, the visibility reported in the historical experiment is a different observable from the simulated fidelity.

## Primary references

- [Bouwmeester et al., Experimental quantum teleportation (1997)](https://doi.org/10.1038/37539) — experimental motivation and conditional photonic transfer.
- [Bennett et al., Teleporting an unknown quantum state (1993)](https://doi.org/10.1103/PhysRevLett.70.1895) — protocol and classical correction message.
- [Massar and Popescu, Optimal extraction of information (1995)](https://doi.org/10.1103/PhysRevLett.74.1259) — optimal qubit state-estimation benchmark.
