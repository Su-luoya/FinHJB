# Unsupported Models

Do not generate misleading FinHJB code for models that exceed the current package boundary.

## Usually Out Of Scope

- two-dimensional or higher-dimensional continuous state spaces
- path-dependent problems that cannot be reduced to one state variable
- models with multiple coupled value functions across discrete regimes
- impulse-control problems requiring intervention operators rather than smooth policy updates
- equilibrium models that need a market-clearing fixed point outside the existing solver loop
- problems whose free-boundary structure cannot be represented with `s_min`, `s_max`, `v_left`, and `v_right`

## Response Pattern

When the model is out of scope:

1. Say clearly that the current FinHJB package is one-dimensional.
2. Name the exact feature that breaks the mapping.
3. Offer the closest implementable simplification if one exists.
4. State what package extension would be required for a faithful implementation.

## Examples

- If the paper has states `(w, z)`, do not collapse `z` into a parameter unless the user explicitly wants that approximation.
- If the model has regime switching with separate value functions `V_G` and `V_B`, explain that current FinHJB does not yet provide a coupled-system interface.
- If the only missing piece is a textual formula from the paper, treat that as an information gap, not an unsupported model.
- If the model is in scope but still requires algebraic derivation before it maps into code, treat that as a derivation gap. Do not silently finish the derivation and jump straight to code; surface the missing steps and confirm them with the user first.
