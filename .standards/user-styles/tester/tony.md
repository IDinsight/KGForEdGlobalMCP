## Python

1. Functions, classes, methods, global variables, etc. should be placed alphabetically within logical groups in each module. Exceptions are allowed when ordering would break execution or make the code difficult to understand, including dependencies, Pydantic validators, and type definitions.
2. When calling functions or methods with multiple arguments, use keyword arguments in alphabetical order, except where the API requires positional arguments. Single-argument calls may use positional arguments.
3. Docstrings are always in NumPy format.
4. Use blank lines to separate logical sections within function and control-block bodies where they improve readability.
5. Always use type hints in function and method signatures. Elsewhere, use them when helpful. The repo's `mypy` tool checks type hints.
6. Never make live API calls in any tests. These should be mocked or stubbed out to the extent possible. If this would seriously degrade the quality of a test, then pause and point this out to me, provide your recommendation(s) and await my decision before writing such a test.
