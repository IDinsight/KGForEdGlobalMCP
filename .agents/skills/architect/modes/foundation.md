# Foundation Architecture

Use when the scope requires establishing or materially redefining the project's
foundational technical structure, major system boundaries, or platform-level
choices.

Focus on decisions that shape later implementation across the project rather
than one bounded capability.

## Design Emphasis

1. Define the major runtime, service, module, persistence, deployment, or
   integration boundaries that implementation must respect.
2. Resolve foundational technology and structural choices only when they
   materially affect the scoped work.
3. Make dependency direction, ownership, lifecycle, and cross-boundary contracts
   explicit where they constrain later design.
4. Identify foundational constraints that future features must inherit without
   turning the design into a general style guide.
5. Keep reversible local implementation choices with Developer.
