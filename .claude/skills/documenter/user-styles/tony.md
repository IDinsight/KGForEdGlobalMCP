# Tony's Documentation Style

Apply only when explicitly selected. These preferences do not override universal
style, correctness, ownership, authoritative project constraints, or protocol
conflict handling.

## Python Docstrings

- Use the NumPy docstring convention for Python docstrings.
- For function and method docstrings created or materially updated, include an
  `Examples` section with one simple happy-path usage example that helps readers
  understand how to use the function or method.
- Examples must reflect actual behavior. Do not invent outputs or claim
  execution that did not occur. Include only necessary setup; an example may
  show usage without an output assertion when no output has been established.
- Do not restyle unrelated docstrings or apply Python docstring sections to
  other document types merely because this profile is selected.
