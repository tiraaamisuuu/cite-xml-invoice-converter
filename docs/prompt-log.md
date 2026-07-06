# Prompt log

This is a short working log for the final project discussion.

## Useful prompts

- "Read the design brief and give me the TLDR before writing code."
- "Break the project into parser, validator, converter, CLI, and UI layers."
- "Build a barebones Python version first, with the core engine separate from
  the CLI."

## Prompts to treat carefully

- "Just map the XML to JSON" is too broad. CITE meaning depends on qualifier
  codes, so every field needs to be cross-checked against the mapping spec.
- "Generate broken tests" needs review. A broken fixture should fail for the
  intended rule, not accidentally fail earlier for an unrelated missing field.
