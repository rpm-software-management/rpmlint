# Testing

The RPMLint test suite has undergone some changes as part of the Google Summer of Code program. These changes can be seen in the links [openSUSE/mentoring#189](https://github.com/openSUSE/mentoring/issues/189) and [rpm-software-management/rpmlint#1101](https://github.com/rpm-software-management/rpmlint/pull/1101). The new test suite uses a mocking strategy to address the issue of relying on binary RPM files. Binary RPM files take a lot of time to unpack and consume real resources like storage in the repository. They also require significant computation when unpacked as individual files.

In this new test suite, we will utilize a `FakePkg` class, which acts as a mock representation of a `Pkg`. This `Pkg` resembles a real RPM file, allowing any test function to use it. Although `FakePkg` is still in its early stages, it can already mock many tests compared to the current implementation.

## `get_tested_mock_package` Function

The `get_tested_mock_package` function's interface is as follows:

```python
def get_tested_mock_package(files=None, real_files=None, header=None)
```

For each new test, we employ the `get_tested_mock_package` function, a helper from `test/Testing.py`. This function leverages the `FakePkg` class to create a mock package named `mockPkg`.

The current implementation of the `get_tested_mock_package` function is as follows:

```python
def get_tested_mock_package(files=None, real_files=None, header=None):
    mockPkg = FakePkg('mockPkg')
    if files is not None:
        mockPkg.create_files(files, real_files)
    if header is not None:
        mockPkg.add_header(header)
    mockPkg.initiate_files_base_data()
    return mockPkg
```

The `get_tested_mock_package` function can accept arguments
- `files`
- `real_files`
- `header`

See the example test function below to get basic idea

```python
@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/lib/python2.7/site-packages/doc': {},
        '/usr/lib/python2.7/site-packages/docs': {},
        '/usr/lib/python3.10/site-packages/doc': {},
        '/usr/lib/python3.10/site-packages/docs': {},
        '/usr/lib64/python2.7/site-packages/doc': {},
        '/usr/lib64/python2.7/site-packages/docs': {},
        '/usr/lib64/python3.10/site-packages/doc': {},
        '/usr/lib64/python3.10/site-packages/docs': {}
    }
)])
def test_python_doc_in_site_packages(package, pythoncheck):
    output, test = pythoncheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: python-doc-in-site-packages /usr/lib/python2.7/site-packages/doc' in out
    # ... (similar assertions for other paths)
```

**`files`**:
`files` argument takes each file's path and a dictionary as shown above `'/usr/lib/python2.7/site-packages/doc': {}` the value part is again a dictionary with file related data such as `create_dirs`, `metadata` and `include_dirs`. `metadata` is yet versatile it can assign any rpm related options or simply rpm file meta data unique to file.

If the content or metadata of the files in the package is not important, it's
possible to use just a list of paths and the files will be created with default
empty content and default flags.


**`real_files`**:
Each of the above file is converted into a `PkgFile` object by default, and into real file only if `real_file` is passed with `True` parameter.

**`header`**:
Header is dictionary object that is specific to rpm file. We can pass specific rpm file header information with this parameter. See [`test_python.py`](https://github.com/afrid18/rpmlint/blob/c7e36548742f94acc9e102dc328605fdea06329c/test/test_python.py#L183) tests for more info
