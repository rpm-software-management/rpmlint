from rpmlint.rpmdiff import Rpmdiff

from Testing import build_tiny_rpm

N_FILES = 50
N_MODE_CHANGED = 10


def _build_diff_pair(tmp_path):
    """
    Build two tiny RPMs with controlled differences: N_FILES files with
    changed content (N_MODE_CHANGED of them also with a changed mode),
    changed content+mode for the two mc files, one added file and a
    changed Summary tag.

    Modes are set with %attr in %files (applied at header generation
    time), not with chmod in %install, so the test does not depend on
    how a given rpmbuild preserves buildroot modes.
    """
    files = [f'/usr/share/diff-test/file{i:02d}' for i in range(N_FILES)]
    mc_files = ['/usr/share/mc/skins/yadt256.ini',
                '/usr/share/mc/syntax/cuda.syntax']
    # files whose mode changes between the two packages
    mode_changed = {f'/usr/share/diff-test/file{i:02d}'
                    for i in range(N_MODE_CHANGED)} | set(mc_files)

    def files_list(attr):
        def entry(path):
            if attr and path in mode_changed:
                return f'%attr(755,root,root) {path}'
            return path
        return '\n'.join([entry(p) for p in files + mc_files])

    oldpkg = build_tiny_rpm(
        tmp_path / 'old', 'diff-test', version='1.0', summary='old summary',
        install_script='\n'.join([
            'mkdir -p %{buildroot}/usr/share/diff-test %{buildroot}/usr/share/mc/skins %{buildroot}/usr/share/mc/syntax',
            'for i in $(seq -w 0 49); do echo "old content $i" > %{buildroot}/usr/share/diff-test/file$i; done',
            'echo "old skin" > %{buildroot}/usr/share/mc/skins/yadt256.ini',
            'echo "old syntax" > %{buildroot}/usr/share/mc/syntax/cuda.syntax',
        ]),
        files_list=files_list(False),
    )
    newpkg = build_tiny_rpm(
        tmp_path / 'new', 'diff-test', version='2.0', summary='new summary',
        install_script='\n'.join([
            'mkdir -p %{buildroot}/usr/share/diff-test %{buildroot}/usr/share/mc/skins %{buildroot}/usr/share/mc/syntax',
            'for i in $(seq -w 0 49); do echo "new content $i" > %{buildroot}/usr/share/diff-test/file$i; done',
            'echo "new skin" > %{buildroot}/usr/share/mc/skins/yadt256.ini',
            'echo "new syntax" > %{buildroot}/usr/share/mc/syntax/cuda.syntax',
            'echo "yaml syntax" > %{buildroot}/usr/share/mc/syntax/yaml.syntax',
        ]),
        files_list=files_list(True) + '\n/usr/share/mc/syntax/yaml.syntax',
    )
    return oldpkg, newpkg


def test_distribution_tags(tmp_path):
    oldpkg, newpkg = _build_diff_pair(tmp_path)
    ignore = []
    diff = Rpmdiff(oldpkg, newpkg, ignore)
    textdiff = diff.textdiff()
    # every changed file plus the added file, the changed Summary tag
    # and the versioned self-provides
    assert len(textdiff.splitlines()) == 56

    ignore.append('T')
    ignore.append('5')
    ignore.append('S')
    diff = Rpmdiff(oldpkg, newpkg, ignore)
    textdiff = diff.textdiff()
    # only mode changes, the added file, the Summary tag and the
    # versioned self-provides are left
    assert len(textdiff.splitlines()) == 16

    assert 'added       /usr/share/mc/syntax/yaml.syntax' in textdiff


def test_exclude(tmp_path):
    oldpkg, newpkg = _build_diff_pair(tmp_path)
    ignore = list('T5S')

    # print(Rpmdiff(oldpkg, newpkg, ignore=ignore).textdiff())

    for exclude in [], ['/usr/share/mc/ski'], ['/share/mc/skins'], ['skins']:
        diff = Rpmdiff(oldpkg, newpkg, ignore, exclude)
        textdiff = diff.textdiff()
        assert '/usr/share/mc/skins/yadt256.ini' in textdiff

    for exclude in (['/usr/share/mc/skins'], ['/usr/share/*/skins'],
                    ['/*/*/*/skins']):
        diff = Rpmdiff(oldpkg, newpkg, ignore, exclude)
        textdiff = diff.textdiff()
        assert '/usr/share/mc/skins/yadt256.ini' not in textdiff
        assert '/usr/share/mc/syntax/cuda.syntax' in textdiff

    for exclude in ['*.syntax'], ['syntax/cuda.syntax']:
        diff = Rpmdiff(oldpkg, newpkg, ignore, exclude)
        textdiff = diff.textdiff()
        assert '/usr/share/mc/skins/yadt256.ini' in textdiff
        assert '/usr/share/mc/syntax/cuda.syntax' not in textdiff
