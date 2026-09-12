---
name: refactor-code
description: "Use when refactoring source code to split oversized files into smaller cohesive modules and standardize formatting without intended behavior changes. Trigger for requests involving files over 1200 lines, code-smell cleanup, duplicated code, long methods, large classes, long parameter lists, feature envy, magic numbers, large-file decomposition, decoupling functional modules, extracting components/helpers/services, consolidating long workflow error handling with Saga/state-machine patterns, adding caching around frequent filesystem reads, improving type coverage with defined types, reorganizing module boundaries, reducing file size, compiling refactored code successfully, running unit/integration tests to prove business logic is unchanged, or applying project formatters during a refactor."
---

# Refactor Code

## Overview

Refactor code in small, reviewable steps that preserve behavior while improving file boundaries, module coupling, workflow reliability, filesystem access patterns, type coverage, and formatting consistency. Prefer the repository's existing architecture, test strategy, exports, and formatter configuration over new conventions.

## Workflow

1. Establish scope, constraints, and acceptance criteria before editing. If the user did not provide a target, inspect the repository and choose the smallest relevant scope; ask only when the expected behavior or public API contract is genuinely unclear.
2. Build a baseline: run or identify focused unit tests, integration tests, compile/build checks, type checks, linters, and formatting checks before refactoring when available. Note any pre-existing failures.
3. Inspect structure with `rg --files`, dependency edges, public exports, tests, and nearby naming conventions. For large-file discovery, smell hints, and formatter hints, run `scripts/refactor_scan.py <repo>`; treat files over 1200 lines as priority split candidates unless generated or intentionally monolithic.
4. Identify concrete smell instances before choosing a refactor: duplicated code, long method, large class, long parameter list, feature envy, magic numbers, or equivalent local patterns. Record file/line evidence and the expected behavior each change must preserve.
5. Choose the smallest behavior-preserving technique that matches the smell: extract method, inline method, introduce explaining variable, replace temp with query, introduce parameter object, remove flag argument, replace conditional with polymorphism, pull up, or push down.
6. Split files by existing responsibility boundaries: UI components, hooks, types, services, adapters, parsing, validation, constants, tests, or domain modules. Keep public entry points stable unless the user explicitly asks for an API change.
7. Decouple functional modules while preserving behavior: isolate pure domain logic from I/O, UI, framework glue, and orchestration; introduce narrow interfaces only where they reduce real dependency pressure.
8. For excessively long workflows with scattered timeout, retry, rollback, or compensation logic, centralize control flow with a Saga/state-machine pattern that makes states, transitions, retry policy, timeout policy, and recovery paths explicit.
9. If business logic repeatedly reads the filesystem, add bounded caching through existing cache utilities when available. Define invalidation, freshness, and test controls before adding the cache.
10. Improve type coverage with defined project types, DTOs, discriminated unions, enums, interfaces, or schemas where the language supports them. Avoid `any`/untyped maps unless generics, interop, or compiler limitations make a narrower type impractical.
11. Move code mechanically first, then adjust imports/exports. Avoid mixing behavior changes with file splitting or formatting.
12. Standardize formatting using the repository's configured formatter or package scripts. Limit formatting scope to touched files unless the user asked for a repository-wide formatting pass.
13. Compile or build the refactored code with the repository's official command before declaring success. Treat new compile errors, import/export errors, module resolution errors, and startup/runtime errors as blockers.
14. Run unit tests and integration tests that cover the refactored business logic. Compare against the baseline so passing tests support the claim that behavior is unchanged.
15. Add or adjust tests only when existing coverage cannot exercise moved logic or critical integration paths. Keep assertions focused on existing behavior, including error paths.
16. Validate with the agreed checks, plus targeted runtime/manual checks for affected workflows when tests are weak.
17. Report changed boundaries, smell instances addressed, refactoring techniques used, compile/build results, unit/integration test results, and any behavior or API risk that remains.

## Resource Routing

- Read `references/refactor-playbook.md` when planning a non-trivial split, checking code smells, choosing refactoring techniques, choosing module boundaries, reducing coupling, introducing Saga/state-machine workflow orchestration, adding filesystem caching, improving type coverage, deciding formatter scope, or handling weak test coverage.
- If present, read `/Users/mac/dev/parseshow/code/parseshow/refactor_code_knowledge.md` for extended smell-to-technique, DDD/layering, workflow, caching, typing, and validation guidance during smell-heavy or architecture-boundary refactors.
- Run `scripts/refactor_scan.py` before broad refactors, when the user asks to find oversized files or code smells, or when scanning for files over the 1200-line bloat threshold.

## Hard Gates

<HARD-GATE>
Do not split files before identifying current public entry points, imports, tests, and formatter commands for the affected area.
</HARD-GATE>

<HARD-GATE>
Do not invent business logic, simplify conditionals, rewrite algorithms, rename public APIs, or change runtime behavior unless the user explicitly requested that behavior change.
</HARD-GATE>

<HARD-GATE>
Do not add Saga/state-machine orchestration, filesystem caching, or new type abstractions until the current workflow behavior, cache freshness requirements, and public type contracts are identified from existing code, tests, docs, or user-provided requirements.
</HARD-GATE>

<HARD-GATE>
Do not apply pattern-heavy refactors such as parameter objects, polymorphism, pull-up, or push-down until a specific smell is located and the existing type hierarchy, call sites, and tests are understood.
</HARD-GATE>

<HARD-GATE>
Do not declare completion without validation evidence: test, typecheck, lint, formatter output, focused manual check, or a clear explanation of why validation could not run.
</HARD-GATE>

<HARD-GATE>
Do not claim behavior is preserved unless compile/build checks and relevant unit and integration tests pass, or unless exact blocking reasons and residual risk are reported.
</HARD-GATE>

## Completion Criteria

- Oversized target files are split into cohesive modules with stable imports and exports.
- Files over 1200 lines are split or a concrete reason is documented for leaving them intact.
- Functional modules are decoupled around stable boundaries without changing runtime behavior.
- Addressed smells are listed with file/line evidence and the specific refactoring technique used.
- Duplicated code, long methods, large classes, long parameter lists, feature envy, and magic numbers are reduced where they affect the requested scope.
- Long workflow error handling is centralized when Saga/state-machine orchestration is warranted.
- Frequent filesystem reads are cached only with explicit freshness and invalidation behavior.
- Defined types cover refactored contracts unless a documented generic or compiler constraint prevents it.
- Refactored code compiles or builds successfully with no new errors.
- Relevant unit tests and integration tests pass and demonstrate unchanged business logic.
- Runtime/startup smoke checks pass when the refactor affects executable entry points, jobs, routes, CLIs, or services.
- Formatting is consistent with existing project tooling.
- Unrelated files and unrelated refactors are left untouched.
- Validation results and any skipped checks are reported clearly.
