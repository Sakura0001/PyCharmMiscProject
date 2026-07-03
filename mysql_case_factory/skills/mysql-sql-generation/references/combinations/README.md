# Combination Matrices

Combination matrices define required baseline SQL shapes for a statement.

Rules:

- A matrix is valid only when its statement reference has already been reviewed
  against MySQL 8.0.22 official documentation.
- Required matrix coverage must pass before derived extension combinations are
  emitted.
- Derived extensions must be marked and must not replace required coverage.
