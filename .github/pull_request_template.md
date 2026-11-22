## Pull Request Description

### Summary of Changes
<!-- Provide a clear, concise summary of the architectural changes, features, or fixes introduced. -->

### Related Issue / Tracking
<!-- Link relevant issue: e.g. Closes #123 -->

### Type of Change
- [ ] `feat`: New feature or analytical capability
- [ ] `fix`: Bug fix or defect correction
- [ ] `refactor`: Code restructuring without behavioral change
- [ ] `test`: Added or updated test suites
- [ ] `docs`: Documentation update
- [ ] `perf`: Memory or computational optimization

---

## Data Science & Integrity Checklist
- [ ] Zero target leakage: No raw identifiers (`flow_id`, `source_ip`, `destination_ip`, `timestamp`) introduced into feature spaces.
- [ ] Pre-split deduplication maintained: Duplicate flows handled to prevent cross-validation data leakage.
- [ ] Non-finite numbers handled: Infinities converted to `NaN` / median imputed.
- [ ] Raw datasets remain strictly immutable and read-only.
- [ ] Zero new third-party dependencies introduced beyond the approved stack.

---

## Engineering & Quality Verification
- [ ] Local tests executed and passing: `pytest tests/ -v`
- [ ] Code syntax validated: Zero syntax errors or circular imports.
- [ ] Application entrypoints verified: `python -m streamlit run app.py` launches cleanly.
- [ ] Documentation updated (`README.md`, `docs/`, docstrings).
