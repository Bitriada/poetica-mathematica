"""rtfa.registry -- the Representation Registry (CTS module 1, PDD section 4).

Each representation is a *Moveset Environment* in the sense of the
"Generative Construction of 6 Geometric Freedoms" (G6GF) paper: it owns a
vocabulary of operations (its moveset), declares what it *cannot* do
(its Incapacity Profile, MBP section 9.2 "Security through Algebraic
Incapability"), and declares how it behaves when a value leaves its
domain (overflow mode).

Two further tables are hardcoded here, both from the source papers:

* the MBP pipeline layers L1-L6 (Monkey Business Pipeline: Flip-Burger,
  Line-Cook, Drink-Runner, Manager, Owner, Tax), and
* the Fare Ladder F0-F5 (monograph Ch. III, section 3.5 "The Fare Ladder:
  Algebraic Atlas"; MBP section 6.3 "What is a number?"):
  binary flag -> cipher -> address -> NaN/register -> set -> instance.

The Level Collision rule (CTS section 5, MBP section 9.6 "Type confusion
as level collision") is evaluated against the Fare Ladder: an operation
whose home rung is above the operand's rung is a collision; a cross-rung
value transfer without an explicit ``cast`` is a collision.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# The Fare Ladder (F0-F5) and the MBP pipeline layers (L1-L6).
# --------------------------------------------------------------------------

FARE_LADDER: dict[int, dict[str, str]] = {
    0: {"name": "Binary Flag", "mbp_layer": 1, "mbp_role": "Flip-Burger (L1)",
        "example": "tally mark / bit", "cast_required_above": 1},
    1: {"name": "Cipher", "mbp_layer": 2, "mbp_role": "Line-Cook (L2)",
        "example": "integer counter", "cast_required_above": 2},
    2: {"name": "Address", "mbp_layer": 3, "mbp_role": "Drink-Runner (L3)",
        "example": "float location", "cast_required_above": 3},
    3: {"name": "NaN (complex register)", "mbp_layer": 4,
        "mbp_role": "Manager (L4)", "example": "complex register",
        "cast_required_above": 4},
    4: {"name": "Set", "mbp_layer": 5, "mbp_role": "Owner (L5)",
        "example": "matrix / tensor", "cast_required_above": 5},
    5: {"name": "Instance", "mbp_layer": 6, "mbp_role": "Tax (L6)",
        "example": "full ledger", "cast_required_above": None},
}

# Home rung of every operation the engine understands (CTS section 5).
# ``cast`` has no home rung: an explicit cast is the *legal* way across
# rungs, so it never collides by itself.
OP_HOME_RUNG: dict[str, int] = {
    "flip": 0, "tally": 0,
    "add": 1, "sub": 1, "mul": 1, "div": 1,
    "pow": 2, "sqrt": 2, "abs": 2,
    "conj": 3, "phase": 3,
    "deref": 2,
    "cast": -1,          # explicit conversion: always legal
}

# Operations that may be *routed* through a higher environment when the
# source environment lacks the vocabulary (PDD section 5, demo 4:
# sqrt of a negative rational routes through the Complex plane).
ROUTED_OPS: dict[str, str] = {"sqrt": "C128"}


@dataclass(frozen=True)
class Representation:
    """One node of the Representation Registry (CTS section 2.1)."""

    id: str
    name: str
    g6gf_env: str                 # N | Z | Q | F | C | UC
    mbp_layer: int                # 1..6
    fare_rung: int                # 0..5 (Fare Ladder)
    moveset: tuple[str, ...]
    incapacity: tuple[str, ...]
    overflow_mode: str            # to_infinity | to_wrap | domain_violation | bend
    limits: dict[str, str] = field(default_factory=dict)
    implemented: bool = True

    def json(self) -> dict:
        return {
            "id": self.id, "name": self.name, "g6gf_env": self.g6gf_env,
            "mbp_layer": self.mbp_layer, "fare_rung": self.fare_rung,
            "fare_rung_name": FARE_LADDER[self.fare_rung]["name"],
            "moveset": list(self.moveset),
            "incapacity": list(self.incapacity),
            "overflow_mode": self.overflow_mode,
            "limits": self.limits,
            "implemented": self.implemented,
        }


U64_MAX = 2**64 - 1
I64_MIN, I64_MAX = -(2**63), 2**63 - 1
F64_MAX = 1.7976931348623157e308
F64_MIN_SUBNORMAL = 5e-324
D128_DIGITS = 34


def _registry() -> dict[str, Representation]:
    R = {}
    nodes = [
        Representation(
            id="BIN", name="binary string (L1 tape)", g6gf_env="N",
            mbp_layer=1, fare_rung=0,
            moveset=("flip", "tally"),
            incapacity=(
                "no arithmetic beyond +1/-1 tally (G6GF section 1: the "
                "binary environment is irreducibly one-dimensional)",
                "multiplication would require combining two counts into "
                "one address, which is not in the moveset",
            ),
            overflow_mode="domain_violation",
            limits={"bits": "8 (one tape cell)"},
        ),
        Representation(
            id="N64", name="natural counter, 64-bit unsigned", g6gf_env="N",
            mbp_layer=2, fare_rung=1,
            moveset=("add", "sub", "mul", "div"),
            incapacity=(
                "no values below 0 (subtraction below zero is a domain "
                "violation)",
                "negative integers reinterpreted as unsigned magnitudes "
                "lose their sign (wrap-around read)",
            ),
            overflow_mode="to_wrap",
            limits={"min": "0", "max": str(U64_MAX)},
        ),
        Representation(
            id="Z64", name="signed integer, 64-bit two's complement",
            g6gf_env="Z", mbp_layer=2, fare_rung=1,
            moveset=("add", "sub", "mul", "div", "cast"),
            incapacity=(
                "no fractions: division with a remainder does not resolve "
                "in Z and bends to Q (G6GF section 2, 3/2)",
                "no irrational roots in its moveset",
            ),
            overflow_mode="to_wrap",
            limits={"min": str(I64_MIN), "max": str(I64_MAX)},
        ),
        Representation(
            id="Q", name="rational, exact (fractions.Fraction)",
            g6gf_env="Q", mbp_layer=3, fare_rung=2,
            moveset=("add", "sub", "mul", "div", "cast"),
            incapacity=(
                "cannot render irrational roots: sqrt(2) has no exact "
                "value here and is approximated (A) or bent toward F/C",
                "no phase: a complex value returning to Q is obfuscated",
            ),
            overflow_mode="bend",
            limits={"min": "none (exact)", "max": "none (exact)"},
        ),
        Representation(
            id="F64", name="IEEE 754 binary64", g6gf_env="F",
            mbp_layer=3, fare_rung=2,
            moveset=("add", "sub", "mul", "div", "pow", "sqrt", "abs",
                     "cast"),
            incapacity=(
                "cannot represent 1/10 exactly (binary mantissa)",
                "cannot preserve the sign of 0 under abs (-0.0)",
                "lacks exact phase representation (requires the C "
                "environment); returning from C applies the [[b]] marker",
                "stuck in transfinite smoothing under nested ^b/sqrt(b): "
                "the Apeirogon (G6GF section 4.6)",
            ),
            overflow_mode="to_infinity",
            limits={"max": repr(F64_MAX),
                    "min_subnormal": repr(F64_MIN_SUBNORMAL)},
        ),
        Representation(
            id="D128", name="IEEE 754 decimal128 (34 significant digits)",
            g6gf_env="F", mbp_layer=3, fare_rung=2,
            moveset=("add", "sub", "mul", "div", "cast"),
            incapacity=(
                "only 34 significant decimal digits: a value needing more "
                "is rounded",
                "cannot render values with infinite decimal expansions "
                "exactly (1/3)",
            ),
            overflow_mode="to_infinity",
            limits={"digits": str(D128_DIGITS)},
        ),
        Representation(
            id="C128", name="complex register (pair of binary64)",
            g6gf_env="C", mbp_layer=4, fare_rung=3,
            moveset=("add", "sub", "mul", "div", "conj", "abs", "phase",
                     "sqrt", "cast"),
            incapacity=(
                "phase is defined modulo 2*pi: position certainty is lost "
                "(Fare Principle)",
                "returning to a real environment destroys the imaginary "
                "part (phase obfuscated, [[b]])",
            ),
            overflow_mode="domain_violation",
            limits={"components": "each as F64"},
        ),
        Representation(
            id="ADDR", name="memory address (F2 location token)",
            g6gf_env="F", mbp_layer=3, fare_rung=2,
            moveset=("deref", "cast"),
            incapacity=(
                "an address is a container, not a number: reading it as a "
                "cipher (Z64) without an explicit cast is a level "
                "collision (CTS section 5, Ptr -> Int in C)",
            ),
            overflow_mode="domain_violation",
            limits={"max": str(U64_MAX)},
        ),
        # Declared but not implemented in v1 (CTS section 10: the Maiden
        # Carry / tau^3 limit is a v2.0 feature).
        Representation(
            id="UC", name="Ultra-Complex (Ch. IV of the monograph)",
            g6gf_env="UC", mbp_layer=4, fare_rung=3,
            moveset=(), incapacity=(
                "declared for v2.0 only: resolves the phase a C128 "
                "obfuscates (Maiden Carry, Lambda = tau^3)",
            ),
            overflow_mode="domain_violation", implemented=False,
        ),
        Representation(
            id="SET", name="set / tensor container (L5)", g6gf_env="F",
            mbp_layer=5, fare_rung=4, moveset=(),
            incapacity=("declared for v2.0 only: L5 Owner objects",),
            overflow_mode="domain_violation", implemented=False,
        ),
    ]
    for r in nodes:
        R[r.id] = r
    return R


REGISTRY: dict[str, Representation] = _registry()

# Environment-name aliases (PDD section 2.1 / CTS section 6.1 write the
# CLI in environment names: "Z:3", "Z -> Q -> F64").
ENV_ALIASES = {"N": "N64", "Z": "Z64", "F": "F64", "C": "C128",
               "D": "D128"}


def get(rep_id: str) -> Representation:
    rep_id = ENV_ALIASES.get(rep_id, rep_id)
    try:
        return REGISTRY[rep_id]
    except KeyError:
        raise KeyError(
            f"unknown representation {rep_id!r}; "
            f"registered: {sorted(REGISTRY)}") from None


def level_collision(op: str, src: Representation,
                    tgt: Representation) -> str | None:
    """Return a collision note, or None if the rung structure is legal.

    CTS section 5: "If an operation maps a value from F2 (Address) to
    F1 (Cipher) without an explicit cast operation, the Classifier
    throws X."  Two sub-rules are enforced here:

    * the operation's home rung must not sit above the operand's rung
      (an L2 multiply executed on L1 binary strings is a collision);
    * a value may not move between rungs without an explicit ``cast``
      (an address dereferenced straight into a cipher is a collision).
    """
    if op == "cast":
        return None
    home = OP_HOME_RUNG.get(op, -1)
    if home > src.fare_rung:
        return (f"op '{op}' lives on rung F{home} "
                f"({FARE_LADDER[home]['name']}), but the operand "
                f"{src.id} is a rung-F{src.fare_rung} "
                f"{FARE_LADDER[src.fare_rung]['name'].lower()}")
    if src.fare_rung != tgt.fare_rung and op not in src.moveset \
            and op not in tgt.moveset:
        return (f"value moved between rungs F{src.fare_rung} and "
                f"F{tgt.fare_rung} without an explicit cast")
    return None


def print_registry() -> str:
    """Human-readable registry dump with the Fare Ladder."""
    lines = []
    lines.append("REPRESENTATION REGISTRY (G6GF moveset environments)")
    lines.append("-" * 78)
    for r in REGISTRY.values():
        if not r.implemented:
            continue
        lines.append(
            f"  {r.id:<5} {r.name:<38} env={r.g6gf_env:<2} "
            f"L{r.mbp_layer}  F{r.fare_rung} "
            f"{FARE_LADDER[r.fare_rung]['name']}")
        lines.append(f"        moveset: {', '.join(r.moveset)}")
        for inc in r.incapacity:
            lines.append(f"        incapacity: {inc}")
    lines.append("")
    lines.append("FARE LADDER (monograph Ch. III, 3.5; MBP 6.3)")
    lines.append("-" * 78)
    for rung, info in FARE_LADDER.items():
        lines.append(f"  F{rung}  {info['name']:<24} {info['mbp_role']:<20}"
                     f" e.g. {info['example']}")
    return "\n".join(lines)
