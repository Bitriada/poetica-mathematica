"""fareoctal -- the Fare-Octal counting system of Poetica Mathematica,
Appendix A, made operational in pure Python (zero dependencies).

    from fareoctal import FareOctal, tau, UNIT, ZERO
    from fareoctal.core import PRIMES

    s = FareOctal.from_value(15)     # tau_3 * tau_5 = tau_{3*5}
    s.display()                      # '[0 0 0 0 0 0 0 0 6]'
    s.to_int()                       # 6 (linear count)
    s.value()                        # 15 (squarefree Fare value)
    s.h_weight()                     # 2^54 (H-tensor spectral embedding)
    FareOctal.from_value(6) * FareOctal.from_value(10)   # ZERO (gcd 2)

See README.md for the three readings, the 117-lattice storage
convention, and the five findings (F1-F5).
"""

from .core import (N_BITS, N_DIGITS, PRIMES, UNIT, ZERO, FareOctal,
                   count_table, index_rule_product, linear_to_tensor,
                   position_of_prime, prime_at, sieve_primes, tau,
                   tensor_to_linear)
from .lattice import (FORTRESS_NOTE, H_EXPONENTS, L_TABLE, M_TABLES,
                      bit_address, digit_address, lattice_sums)
from .algebra import (FareElement, functional_equation_identities,
                      spectral_involution, zeta_element)

__version__ = "1.0.0"

__all__ = [
    "N_BITS", "N_DIGITS", "PRIMES", "UNIT", "ZERO", "FareOctal", "tau",
    "count_table", "index_rule_product", "linear_to_tensor",
    "position_of_prime", "prime_at", "sieve_primes", "tensor_to_linear",
    "FORTRESS_NOTE", "H_EXPONENTS", "L_TABLE", "M_TABLES", "bit_address",
    "digit_address", "lattice_sums", "FareElement",
    "functional_equation_identities", "spectral_involution",
    "zeta_element", "__version__",
]
