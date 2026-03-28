# Unified Delivery Guard Report

- Phase: `final`
- Mode: `questionBank`
- Status: `FAIL`
- Task: 学生端10端对齐终检（subagent全收口）
- Failed Checks: `1`
- Waived Checks: `0`
- Missing Domains: `none`

## Domain Summary
- `Field Standards`: `PASS` (configured=9, failed=0, waived=0)
- `API Standards`: `PASS` (configured=13, failed=0, waived=0)
- `Page Standards`: `PASS` (configured=21, failed=0, waived=0)
- `Status Standards`: `PASS` (configured=8, failed=0, waived=0)
- `Permission Standards`: `PASS` (configured=11, failed=0, waived=0)
- `Validation Standards`: `PASS` (configured=7, failed=0, waived=0)
- `Error Standards`: `PASS` (configured=9, failed=0, waived=0)
- `Extension Standards`: `PASS` (configured=11, failed=0, waived=0)
- `Documentation Standards`: `PASS` (configured=13, failed=0, waived=0)
- `Test Standards`: `FAIL` (configured=20, failed=1, waived=0)

## Failed Checks
- `test` / `runtime:pytest`: .......................................                                  [100%]
39 passed in 1.74s
...............................................                          [100%]
=============================== warnings summary ===============================
tests/integration/test_batch_parse_api.py::test_batch_parse_uses_docx_image_ocr_fallback_for_formula_content
  /Users/shaotongli/Code/newaitiku/.venv/lib/python3.9/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
    warnings.warn(

tests/integration/test_batch_parse_api.py::test_batch_parse_uses_docx_image_ocr_fallback_for_formula_content
  /Users/shaotongli/Code/newaitiku/.venv/lib/python3.9/site-packages/albumentations/__init__.py:24: UserWarning: A new version of Albumentations is available: 2.0.8 (you have 1.4.24). Upgrade using: pip install -U albumentations. To disable automatic update checks, set the environment variable NO_ALBUMENTATIONS_UPDATE to 1.
    check_for_updates()

tests/integration/test_batch_parse_api.py::test_batch_parse_uses_docx_image_ocr_fallback_for_formula_content
  /Users/shaotongli/Code/newaitiku/.venv/lib/python3.9/site-packages/pydantic/main.py:214: DeprecationWarning: value is deprecated, use fill instead
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)

tests/integration/test_batch_parse_api.py::test_batch_parse_uses_docx_image_ocr_fallback_for_formula_content
  /Users/shaotongli/Code/newaitiku/.venv/lib/python3.9/site-packages/albumentations/core/validation.py:45: DeprecationWarning: ShiftScaleRotate is deprecated. Please use Affine transform instead.
    original_init(self, **validated_kwargs)

tests/integration/test_batch_parse_api.py::test_batch_parse_uses_docx_image_ocr_fallback_for_formula_content
  /Users/shaotongli/Code/newaitiku/.venv/lib/python3.9/site-packages/pydantic/main.py:426: UserWarning: Pydantic serializer warnings:
    Expected `dict[str, any]` but got `UniformParams` with value `UniformParams(noise_type=... 0.058823529411764705)])` - serialized value may not be as expected
    return self.__pydantic_serializer__.to_python(

tests/integration/test_batch_parse_api.py::test_batch_parse_uses_docx_image_ocr_fallback_for_formula_content
  /Users/shaotongli/Code/newaitiku/.venv/lib/python3.9/site-packages/pydantic/main.py:214: DeprecationWarning: `var_limit` deprecated. Use `std_range` instead.
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)

tests/integration/test_batch_parse_api.py::test_batch_parse_uses_docx_image_ocr_fallback_for_formula_content
  /Users/shaotongli/Code/newaitiku/.venv/lib/python3.9/site-packages/pydantic/main.py:214: DeprecationWarning: `quality_lower` is deprecated. Use `quality_range` as tuple (quality_lower, quality_upper) instead.
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)

tests/integration/test_batch_parse_api.py::test_batch_parse_uses_docx_image_ocr_fallback_for_formula_content
tests/integration/test_batch_parse_api.py::test_batch_parse_uses_docx_image_ocr_fallback_for_formula_content
  /Users/shaotongli/Code/newaitiku/.venv/lib/python3.9/site-packages/albumentations/core/validation.py:45: DeprecationWarning: always_apply is deprecated. Use `p=1` if you want to always apply the transform. self.p will be set to 1.
    original_init(self, **validated_kwargs)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
47 passed, 9 warnings in 65.30s (0:01:05)
........................................................................ [ 41%]
........................................................................ [ 83%]
............................                                             [100%]
172 passed in 238.22s (0:03:58)
.................F.                                                      [100%]
=================================== FAILURES ===================================
__________ test_student_wrong_book_true_click_filter_batch_and_detail __________

tmp_path_factory = TempPathFactory(_given_basetemp=None, _trace=<pluggy._tracing.TagTracerSub object at 0x113d37040>, _basetemp=PosixPath...rs/2l/4vlksfvd7sdd2_plt_wv52680000gn/T/pytest-of-shaotongli/pytest-1672'), _retention_count=3, _retention_policy='all')

    @pytest.mark.e2e
    def test_student_wrong_book_true_click_filter_batch_and_detail(tmp_path_factory: pytest.TempPathFactory) -> None:
        if shutil.which("npm") is None:
            pytest.skip("未检测到 npm，跳过前端 UI 自动化用例。")
    
        db_path = tmp_path_factory.mktemp("student-wrong-book-flow") / "question_bank.db"
        backend_port = _pick_free_port()
        frontend_port = _pick_free_port()
        backend_base_url = f"http://127.0.0.1:{backend_port}"
        frontend_base_url = f"http://127.0.0.1:{frontend_port}"
    
        backend_command = [
            sys.executable,
            str(ROOT_DIR / "tools/python/click_replay_server.py"),
            "--host",
            "127.0.0.1",
            "--port",
            str(backend_port),
            "--db-path",
            str(db_path),
        ]
        backend_env = os.environ.copy()
        backend_env["QB_CORS_ORIGINS"] = frontend_base_url
        backend_process = subprocess.Popen(
            backend_command,
            cwd=str(ROOT_DIR),
            env=backend_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    
        frontend_env = os.environ.copy()
        frontend_env["VITE_API_BASE_URL"] = backend_base_url
        frontend_command = [
            "npm",
            "run",
            "dev",
            "--",
            "--host",
            "127.0.0.1",
            "--port",
            str(frontend_port),
            "--strictPort",
        ]
        frontend_process = subprocess.Popen(
            frontend_command,
            cwd=str(FRONTEND_DIR),
            env=frontend_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    
        try:
            _wait_until_ready(f"{backend_base_url}/login")
            _wait_until_ready(f"{frontend_base_url}/login")
            with sync_playwright() as playwright_driver:
                request_context = _new_student_request_context(playwright_driver, backend_base_url)
                level3_node_id, level3_label = _resolve_wrong_book_filter_path(request_context)
                browser = playwright_driver.chromium.launch(headless=True)
                try:
                    page = browser.new_page(viewport={"width": 1440, "height": 960})
                    _login_student(page, frontend_base_url)
                    _open_student_nav(
                        page,
                        "我的题库",
                        "/student/question-bank/repair",
                        current_heading := "错题中心",
                        "详细错题库",
                    )
                    expect(page.get_by_role("heading", name=current_heading)).to_be_visible()
                    expect(page.get_by_text("批量处理").first).to_be_visible()
    
                    page.locator(".knowledge-cascader .el-input__wrapper").click()
                    _wait_for_global_loading_mask(page)
                    cascader_labels = page.locator(".el-cascader__dropdown .el-cascader-node__label")
>                   expect(cascader_labels.first).to_be_visible()
E                   AssertionError: Locator expected to be visible
E                   Actual value: None
E                   Error: element(s) not found 
E                   Call log:
E                     - Expect "to_be_visible" with timeout 5000ms
E                     - waiting for locator(".el-cascader__dropdown .el-cascader-node__label").first

tests/e2e/test_student_true_click_ui.py:764: AssertionError
=========================== short test summary info ============================
FAILED tests/e2e/test_student_true_click_ui.py::test_student_wrong_book_true_click_filter_batch_and_detail
1 failed, 18 passed in 170.89s (0:02:50)
[run] unit: tests/unit
[run] integration: tests/integration
[run] regression: tests/regression tests/test_question_bank.py
[run] e2e: tests/e2e
[fail] e2e exited with code 1

## questionBank Module Summary
- `user`: `PASS` (schema=True, contractDoc=True, extJson=True)
- `userAuth`: `PASS` (schema=True, contractDoc=True, extJson=True)
- `knowledge`: `PASS` (schema=True, contractDoc=True, extJson=True)
- `question`: `PASS` (schema=True, contractDoc=True, extJson=True)
- `task`: `PASS` (schema=True, contractDoc=True, extJson=True)