## Python

1. Functions, classes, methods, global variables, etc. should be placed alphabetically within logical groups in each module. Exceptions are allowed when ordering would break execution or make the code difficult to understand, including dependencies, Pydantic validators, and type definitions.
2. When calling functions or methods with multiple arguments, use keyword arguments in alphabetical order, except where the API requires positional arguments. Single-argument calls may use positional arguments.
3. Docstrings are always in NumPy format. Include a short `Examples` section showing how the function or method is typically invoked and what output it produces.
4. Use blank lines to separate logical sections within function and control-block bodies where they improve readability.
5. Keep McCabe complexity <= 10. This is checked by the repo's `pylint` tool.
6. Always use type hints in function and method signatures. Elsewhere, use them when helpful. The repo's `mypy` tool checks type hints.
7. Use inline comments where helpful to explain complex or tricky code.
