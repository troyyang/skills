# Refactor Playbook

## Usage Examples

1. User asks: "This 900-line React page is hard to maintain. Split it into smaller files and run formatting." Expected behavior: extract components, hooks, types, and helpers following local conventions; preserve route behavior and exports; run the relevant formatter, lint, compile/typecheck, and focused unit/integration UI tests.
2. User asks: "Refactor this large Python service module and standardize formatting." Expected behavior: separate API client, parsing, validation, constants, and public facade while preserving function signatures; run black/ruff/pytest plus the repository's compile/import checks where available.
3. User asks: "This 5000-line worker has retries and timeout handling scattered everywhere." Expected behavior: identify the current states and failure paths, extract cohesive modules, and centralize orchestration through the repository's existing workflow/state-machine conventions or a minimal Saga-style coordinator.
4. User asks: "This business service reads config files in every operation." Expected behavior: preserve read semantics, add bounded caching around filesystem reads using existing cache utilities when available, define invalidation/freshness behavior, and test stale/missing/changed-file cases.
5. User asks: "Check this module for duplicated code, long methods, large classes, long parameter lists, feature envy, and magic numbers, then refactor safely." Expected behavior: run the smell scan, confirm heuristics against source, apply the smallest matching refactoring techniques, and validate compile/unit/integration checks.

## Trigger Boundaries

Use this skill for source-code refactors where file size, code-smell cleanup, module cohesion, functional decoupling, workflow orchestration cleanup, filesystem-read caching, type coverage, or formatting consistency is the main goal.

Do not use it for feature implementation, bug fixes, migrations, dependency upgrades, open-ended performance rewrites, architecture redesigns, generated-code cleanup, or style-only prose/document formatting unless file splitting, code-smell cleanup, decoupling, workflow cleanup, filesystem caching, type coverage, or source formatter standardization is part of the task.

Required inputs are the target repository and either a user-provided scope or enough local context to infer a small target area. Expected outputs are edited source files, stable behavior, successful compile/build evidence, unit and integration test evidence for affected business logic, and a concise summary of the new boundaries.

## Splitting Heuristics

- Treat files over 1200 lines as bloated by default. Split them unless they are generated, vendored, schema snapshots, machine-authored fixtures, or the repository has an explicit reason to keep them monolithic.
- For files below 1200 lines, split only when cohesion, ownership, testability, or readability improves enough to justify the churn.
- Prefer existing seams already visible in imports, tests, comments, route sections, class/function groups, types, and naming.
- Keep orchestration near the original entry point; move leaf utilities and cohesive subcomponents first.
- Create folders only when the local codebase already uses folder-per-feature or the extracted set has multiple related files.
- Keep barrel files and public exports compatible when callers depend on them.
- Move tests with the code only when the repository already colocates tests; otherwise update existing tests in place.
- Avoid introducing new dependency direction. Lower-level modules must not import higher-level orchestration modules.
- Avoid splitting tightly coupled code solely to meet a line-count target. Cohesion matters more than exact size.

## Code Smell Review

Use `scripts/refactor_scan.py <repo>` for first-pass heuristics, then confirm each candidate by reading the source. Heuristic output is evidence to inspect, not permission to edit blindly.

For the expanded smell-to-technique matrix and DDD/layering decision table in this workspace, read `/Users/mac/dev/parseshow/code/parseshow/refactor_code_knowledge.md` when that file exists.

- Duplicated code: prefer extracting shared behavior when duplicate branches are truly the same rule; keep separate copies when similar code represents different business concepts likely to diverge.
- Long method: extract named steps around intention-revealing chunks, validation, mapping, I/O, retry loops, and error handling. Preserve local order and side effects.
- Large class: split responsibilities by SRP: orchestration, domain decisions, persistence, transport, formatting, validation, or presentation.
- Long parameter list: introduce a parameter object only when parameters are passed together repeatedly or represent one concept. Avoid hiding unrelated arguments in a vague options bag.
- Feature envy: move behavior closer to the data owner or add a narrow method on that owner only when it matches existing object responsibilities.
- Magic numbers: replace unexplained literals with named constants, enums, config, or domain terms. Do not rename obvious idioms such as indexes or simple boolean thresholds unless meaning is unclear.

## Refactoring Techniques

- Extract Method: use for complex logic that has a clear intention and can be tested or reviewed independently.
- Inline Method: use when an extracted function obscures more than it explains.
- Introduce Explaining Variable: use for complex conditions or calculations when naming subexpressions makes business rules clearer.
- Replace Temp with Query: use when repeated temporary calculations can become a side-effect-free helper without changing evaluation semantics.
- Introduce Parameter Object: use for stable groups of parameters, especially date ranges, pagination, retry options, or workflow context.
- Remove Flag Argument: split boolean-controlled functions into explicit functions when callers are choosing different behaviors.
- Replace Conditional with Polymorphism: use for stable type- or strategy-based branching; avoid it for volatile one-off conditionals.
- Pull Up or Push Down: move shared fields/methods up or specialized behavior down only after reviewing the hierarchy and callers.

## Decoupling Guidelines

- Separate domain decisions from framework glue, UI rendering, transport, persistence, filesystem access, and environment lookup.
- Prefer dependency injection through existing constructors, parameters, context objects, or service registries over global imports when it breaks cycles or enables focused tests.
- Keep extracted modules at one abstraction level. Do not create helpers that import back into the original orchestration file.
- Preserve public facades when callers depend on a legacy import path; re-export extracted implementation from the old entry point when needed.
- Add interfaces or protocols only when there are multiple implementations, tests need substitution, or an existing architectural boundary already expects one.

## Workflow Orchestration

Use Saga/state-machine orchestration only when a workflow has multiple steps plus scattered timeout, retry, rollback, compensation, or resumability logic. Avoid adding it to simple straight-line code.

- First map existing states, transitions, side effects, timeout values, retry limits, idempotency keys, compensation steps, and terminal failure states from code, tests, logs, or docs.
- Prefer existing workflow engines, job frameworks, state-machine libraries, or local conventions already used in the repository.
- Keep side effects in step handlers and orchestration policy in the Saga/state machine. Step handlers should be independently testable and should not own global retry loops.
- Make retry and timeout policy explicit and centralized. Keep per-step exceptions only when business rules require them.
- Test success, retry exhaustion, timeout, cancellation, compensation, and resume/replay paths when those behaviors exist.

## Filesystem Caching

Add caching for frequent business-logic filesystem reads only after identifying current read semantics and correctness constraints.

- Prefer existing cache utilities, memoization helpers, file watchers, or configuration loaders.
- Define cache key, TTL or invalidation trigger, maximum size, concurrency behavior, error behavior, and test reset hooks.
- Preserve required freshness for files that may change during a process. If immediate freshness is required, avoid caching or add explicit invalidation based on mtime/content hash.
- Do not cache secrets, permission-sensitive reads, or user-specific files unless the existing security model supports it.
- Test cache hit, cache miss, missing file, changed file, invalidation, and read-error cases.

## Type Coverage

- Use defined project types for extracted contracts: interfaces, type aliases, DTOs, enums, discriminated unions, dataclasses, protocols, schemas, or language equivalents.
- Replace broad untyped values only when the actual shape can be derived from code, tests, schemas, or public docs.
- Avoid `any`, raw dictionaries/maps, stringly typed states, and untyped callback signatures when a narrow type is practical.
- Allow generics, unknown/opaque types, framework interop types, or temporary compiler workarounds when stricter types would be misleading or block compilation.
- Run the repository's typecheck or compile step after type-boundary changes.

## Formatting Rules

- Discover existing formatter tooling before formatting: package scripts, `pyproject.toml`, `.prettierrc`, `.editorconfig`, `go fmt`, `cargo fmt`, `dotnet format`, or language-specific config.
- Prefer official project commands such as `npm run format`, `pnpm format`, `ruff format`, `black`, `gofmt`, or equivalent scripts already present in the repo.
- Format touched files first. Format the whole repository only when the user requests it or the existing formatter command cannot target files and the blast radius is acceptable.
- Do not add a new formatter or config unless the user explicitly asks and acceptance criteria include it.

## Validation Ladder

Run the narrowest meaningful checks first, then broaden if the touched surface requires it. Preserve baseline behavior by comparing post-refactor results with pre-refactor results and by treating new failures as blockers.

1. Formatter or format check for touched files.
2. Compile/build or import/load check for the affected package/module.
3. Lint or typecheck for affected package/module.
4. Focused unit/component tests covering moved code and existing business rules.
5. Integration tests covering changed module boundaries, I/O adapters, workflows, jobs, routes, API calls, and persistence interactions.
6. Broader package test suite when public exports, routing, shared utilities, workflow orchestration, or build config changed.
7. Runtime/startup smoke check when executable entry points, services, CLIs, jobs, routes, or bundled artifacts changed.

For behavior preservation:

- Run existing unit tests before and after when practical; do not rewrite assertions to match refactor mistakes.
- Prefer adding characterization tests before moving code when business rules are implicit or coverage is weak.
- Cover success, validation failure, dependency failure, retry exhaustion, timeout, cancellation, cache invalidation, and integration boundaries when those paths are affected.
- Do not mark the refactor complete while new compile errors, runtime startup errors, or unit/integration regressions remain unresolved.

If validation cannot run, record the exact command attempted, the reason it failed, and the residual risk.
