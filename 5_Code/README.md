# 5. Code & Computational Artifacts

Welcome to the code section of *Poetica Mathematica*. 

> ⚠️ **READ THIS FIRST**
> 
> **These are not standard software libraries.** They are executable extensions of the mathematical and philosophical theories presented in the monograph. 
> 
> If you just look at the Python files, you will likely be confused. The code uses custom syntax, non-standard logic (e.g., deliberately blocking certain mathematical operations), and philosophical terminology (e.g., "Fare," "Apeirogon," "Type Confusion"). 
> 
> **To understand what you are looking at, you must read the specific `README.md` inside each project folder before running the code.** The context is not just recommended; it is required to understand why the code behaves the way it does.

---

## The Two Artifacts

This folder contains two distinct computational models, each corresponding to a standalone paper:

### 1. [Lattice 117 (`/Lattice_117`)](./Lattice_117/README.md)
A generative integer fractal. It builds a 117-point combinatorial object from a single seed (2) and verifies the hyperoperation ladder. It proves the structural claims of the *Generative Integer Fractal* paper—from the 9 base points up to exact power towers that outscale the Fast-Growing Hierarchy.

### 2. [Fare-Audit (`/Fare_Audit`)](./Fare_Audit/README.md)
A read-only auditor for lossy type conversions. It acts as a flight recorder for the Monkey Business Pipeline (MBP). It prevents type-confusion (level collisions) algebraically, calculates exact error vectors (the "Fare") when numbers are cast between environments (e.g., `Q` to `F64`), and logs the transitions in a tamper-evident, nilpotent ledger (`τ²=0`).

---

## The Source Papers

The mathematical rules implemented in this code are detailed in the following standalone papers:

*   **For Lattice 117:** [Generative Integer Fractal from minimal rules](https://github.com/Bitriada/poetica-mathematica/blob/main/3_Standalone_papers/Arithmetic_Bitriada/Generative_Integer_Fractal_from_minimal_rules.pdf)
*   **For Fare-Audit:** [Monkey Business Arithmetic Spectator Pipeline](https://github.com/Bitriada/poetica-mathematica/blob/main/3_Standalone_papers/Monkey_Business/Monkey_business_arithmetic_spectator_pipeline.pdf)

## Reproducibility & Testing
Both projects are self-verifying. Because they rely on exact mathematics, you do not need to install anything locally. Both folders are equipped with **GitHub Actions**. You can verify the mathematical integrity of both objects directly in your browser by navigating to the **Actions** tab at the top of this repository. 

Each individual project README explains exactly how to trigger these automated tests and how to feed the programs new, custom inputs to test them yourself.
