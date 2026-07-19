Status: DONE

Commits made:
- ee7febc feat: add Python AST adapter

Test summary:
- 5 tests collected and passed
- test_python_adapter_language: PASSED
- test_python_adapter_extensions: PASSED
- test_parse_god_class: PASSED
- test_parse_feature_envy: PASSED
- test_parse_dip_violation: PASSED

Any concerns:
- The commit inadvertently included __pycache__ files and other pre-existing project artifacts (.superpowers files, etc.) alongside the intended changes. This does not affect functionality but may clutter the commit history. A future cleanup could squash or remove these if desired.
