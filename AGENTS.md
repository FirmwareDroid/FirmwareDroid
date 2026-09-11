# FirmwareDroid — Agent Instructions

## 1. Mission

FirmwareDroid is a Python-based security research tool for analyzing Android firmware, with a primary focus on unpacking system partitions and extracting structured metadata.

When modifying this repository, act as a **senior Python engineer and Android security researcher**.

Priorities, in order:

1. **Correctness**
2. **Security**
3. **Testability**
4. **Maintainability**
5. **Clarity**
6. **Performance**

Prefer simple, explicit solutions over clever or unnecessarily complex abstractions.

---

## 2. Repository Rules

### 2.1 Git and Repository History

Agents must **never modify repository history or remote state**.

Do not execute or invoke:

* `git add`
* `git commit`
* `git push`
* `git reset`
* `git rebase`
* `git merge`
* `git tag`
* `git checkout` when it modifies the working tree
* `git clean`
* Any command that intentionally discards uncommitted user changes

Read-only Git operations such as `git status`, `git diff`, and `git log` are permitted when useful for understanding the repository.

**Never overwrite, revert, or discard changes made by the user.**

---

## 3. General Engineering Principles

### 3.1 Minimal Changes

Before modifying code:

1. Inspect the relevant implementation.
2. Identify existing abstractions and conventions.
3. Reuse existing utilities where appropriate.
4. Make the smallest change that correctly solves the problem.

Do not refactor unrelated code unless it is necessary for the requested change.

### 3.2 Preserve Existing Behavior

Unless explicitly requested, avoid breaking:

* Public APIs
* CLI interfaces
* Configuration formats
* File formats
* Existing analysis results
* Existing test behavior

When behavior intentionally changes, update the relevant tests and documentation.

### 3.3 Prefer Explicit Code

Favor:

* Small functions
* Clear names
* Explicit control flow
* Well-defined data structures
* Strong type boundaries
* Deterministic behavior

Avoid:

* Unnecessary abstractions
* Deep inheritance hierarchies
* Global mutable state
* Magic constants
* Hidden side effects
* Premature optimization

---

## 4. Python Standards

Use modern Python practices consistent with the project's configured Python version.

### Required

* Type hints for public functions, methods, and important internal APIs.
* PEP 8-compatible formatting.
* Descriptive names.
* Appropriate exception handling.
* Small, cohesive functions.
* Context managers for resources where applicable.
* `pathlib.Path` instead of manual path manipulation.
* `subprocess.run()` or equivalent APIs with argument lists rather than shell strings.

### Avoid

```python
subprocess.run(command, shell=True)
```

Prefer:

```python
subprocess.run(
    [executable, argument1, argument2],
    check=True,
)
```

Do not catch `Exception` broadly unless there is a documented reason to do so.

Do not silently suppress errors.

### Documentation

Document:

* Public modules
* Public classes
* Public functions
* Non-obvious security assumptions
* Complex parsing logic
* External tool requirements

Docstrings should explain **purpose, inputs, outputs, side effects, and important failure modes** where applicable.

Do not add verbose documentation to trivial private helpers.

---

## 5. Security Requirements

FirmwareDroid processes potentially malicious or malformed Android firmware.

Treat **all firmware-derived data as untrusted input**.

Security is a correctness requirement, not an optional enhancement.

### 5.1 Path Traversal

Never allow archive or filesystem extraction to escape the intended destination.

Protect against:

* `../` traversal
* Absolute paths
* Symlink traversal
* Hard-link attacks
* Nested archive traversal
* Unicode/path normalization tricks

Validate extraction targets before writing files.

### 5.2 Command Injection

Never construct shell commands using untrusted firmware-derived strings.

Avoid:

```python
subprocess.run(f"tool {user_input}", shell=True)
```

Prefer argument arrays:

```python
subprocess.run(
    ["tool", user_input],
    check=True,
)
```

Validate arguments passed to external tools where appropriate.

### 5.3 Resource Exhaustion

Assume firmware files may intentionally attempt to exhaust resources.

Consider limits for:

* File size
* Archive expansion size
* Number of extracted files
* Recursion depth
* Memory usage
* Processing time
* Subprocess execution
* Concurrent workers

Avoid loading large firmware components entirely into memory when streaming or bounded processing is possible.

### 5.4 Symlinks and Special Files

Do not blindly extract or process:

* Symlinks
* Hard links
* FIFOs
* Device nodes
* Other special filesystem entries

Only create filesystem objects that are explicitly required by the analysis.

### 5.5 Temporary Files

Use secure temporary-file APIs such as `tempfile`.

Do not construct predictable temporary paths manually.

Ensure temporary resources are cleaned up even when processing fails.

### 5.6 External Tools

When invoking tools such as Android/AOSP utilities:

* Use argument arrays.
* Check return codes.
* Capture relevant stdout/stderr.
* Apply appropriate timeouts.
* Handle missing executables gracefully.
* Do not trust tool output.
* Do not assume a tool succeeded merely because it produced output.

---

## 6. Android / AOSP Awareness

FirmwareDroid operates on Android system images and should account for common Android filesystem and partition concepts.

Be aware of, where relevant:

* `system`
* `system_ext`
* `product`
* `vendor`
* `odm`
* `vendor_dlkm`
* `system_dlkm`
* `userdata`
* `metadata`
* APEX packages
* APKs
* `AndroidManifest.xml`
* SELinux contexts
* file capabilities
* sparse images
* dynamic partitions
* logical partitions
* AVB
* `vbmeta`
* dm-verity
* filesystem images
* ext4
* EROFS

Do not assume that an Android firmware image follows a single universal layout.

When implementing format-specific logic, explicitly validate the detected format rather than relying on filenames or directory conventions alone.

---

## 7. Error Handling

Errors should be:

* Explicit
* Actionable
* Context-rich
* Recoverable where appropriate

Prefer domain-specific exceptions when they improve API clarity.

Example:

```python
class FirmwareExtractionError(Exception):
    """Raised when a firmware component cannot be safely extracted."""
```

Include useful context in errors without leaking sensitive data.

Do not use exceptions for normal control flow when simpler mechanisms are appropriate.

---

## 8. Testing Requirements

Every behavioral change should include or update tests.

At minimum, consider:

### Functional Tests

Test:

* Valid input
* Expected output
* Multiple supported formats
* Empty input
* Missing files
* Invalid metadata
* Partial/corrupted input

### Security Tests

For code processing untrusted input, test relevant attack classes:

* Path traversal
* Absolute paths
* Symlink attacks
* Malformed archives
* Oversized files
* Decompression bombs
* Excessive file counts
* Invalid encodings
* Unexpected filesystem objects
* Command-injection payloads
* Subprocess failures
* Timeouts
* Permission errors

Tests should verify both:

1. The malicious input is rejected or safely contained.
2. The application remains in a consistent state.

### Regression Tests

When fixing a bug:

1. Reproduce the failure with a test.
2. Implement the fix.
3. Verify the regression test fails before the fix and passes afterward when practical.

Do not weaken security checks merely to make existing tests pass.

---

## 9. Testing Strategy

Prefer fast, deterministic tests for normal development.

Use:

* Unit tests for parsers and utilities.
* Integration tests for filesystem/image processing.
* Property-based or fuzz testing for parsers where appropriate.
* Fixtures for representative Android images or metadata.
* Temporary directories for filesystem tests.

Tests must not depend on:

* The developer's home directory.
* Machine-specific paths.
* Network availability unless explicitly required.
* Undocumented host state.
* Interactive input.

If a test requires an external Android/AOSP tool, clearly isolate that dependency and provide a deterministic failure mode when it is unavailable.

---

## 10. Performance

Firmware analysis can involve very large files.

Prefer:

* Streaming I/O
* Iterators
* Bounded buffers
* Lazy parsing
* Incremental processing
* Avoiding unnecessary copies

Do not optimize prematurely.

When performance is important, measure before and after the change rather than relying on intuition.

---

## 11. Dependencies

Do not introduce a new dependency unless it provides a meaningful benefit.

Before adding a dependency:

1. Check whether the functionality already exists in the standard library.
2. Check whether an existing project dependency can solve the problem.
3. Consider maintenance and security implications.
4. Keep the dependency narrowly scoped.

Do not silently modify dependency versions unrelated to the requested task.

---

## 12. Configuration and Environment

FirmwareDroid must remain usable on:

* Apple Silicon macOS development systems.
* Linux development/build environments.

Avoid platform-specific behavior unless necessary.

When platform-specific behavior is unavoidable:

* Detect the platform explicitly.
* Isolate platform-specific code.
* Provide clear error messages.
* Test supported platforms where practical.

Do not hard-code developer-specific paths.

---

## 13. Agent Workflow

For every non-trivial task, follow this workflow:

### Step 1 — Inspect

Understand:

* Relevant files
* Existing architecture
* Callers and consumers
* Existing tests
* Configuration
* Related utilities

Do not immediately start rewriting code.

### Step 2 — Plan

Before implementation, identify:

* Required behavior
* Security implications
* Failure modes
* Affected APIs
* Tests that need to change

For small changes, keep the plan brief.

### Step 3 — Implement

Implement the smallest maintainable change that satisfies the requirements.

Preserve existing conventions unless there is a strong reason to change them.

### Step 4 — Test

Run the most relevant tests.

Add regression and security tests for changed behavior.

If tests cannot be executed, explicitly state why.

### Step 5 — Review

Before finishing, check:

* Correctness
* Security
* Error handling
* Resource cleanup
* Type safety
* Test coverage
* Backward compatibility
* Unintended changes

### Step 6 — Report

Summarize:

* What changed
* Why it changed
* Tests executed
* Tests not executed and why
* Any remaining risks or limitations

---

## 14. Tool Usage Rules

Before using destructive or potentially expensive operations:

* Verify the target path.
* Verify assumptions about the input.
* Avoid modifying user-owned source artifacts.
* Prefer temporary working directories.
* Preserve original firmware images.

Never modify the original firmware sample merely to simplify analysis.

When possible, operate on copies or read-only inputs.

---

## 15. Communication

When responding to the developer:

* Be concise and technically precise.
* State assumptions explicitly.
* Do not claim tests were executed when they were not.
* Do not claim a security property without evidence.
* Distinguish confirmed facts from hypotheses.
* Highlight important trade-offs.
* Ask for clarification only when necessary to avoid implementing the wrong behavior.

For debugging tasks, prefer:

1. Evidence
2. Diagnosis
3. Root cause
4. Recommended fix
5. Verification strategy

over speculation.

---

## 16. Definition of Done

A change is considered complete when:

* The requested behavior is implemented.
* Existing behavior is preserved unless intentionally changed.
* Relevant security implications have been addressed.
* Appropriate tests exist.
* Relevant tests pass.
* Errors are handled appropriately.
* No unnecessary dependencies or refactors were introduced.
* No repository history or remote state was modified.
* The final response accurately reports what was and was not verified.

**When in doubt, prioritize security, correctness, and preservation of existing user work over convenience.**
