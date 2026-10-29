from rpmlint.rpmdiff import Rpmdiff

from Testing import get_tested_path


def test_distribution_tags():
    oldpkg = get_tested_path('binary/mc-4.8.15-10.3.1.x86_64.rpm')
    newpkg = get_tested_path('binary/mc-4.8.21-2.1.x86_64.rpm')
    ignore = []
    diff = Rpmdiff(oldpkg, newpkg, ignore)
    textdiff = diff.textdiff()
    # the count always reports one less
    assert 231 <= len(textdiff.splitlines()) <= 233

    ignore.append('T')
    ignore.append('5')
    ignore.append('S')
    diff = Rpmdiff(oldpkg, newpkg, ignore)
    textdiff = diff.textdiff()
    assert 36 <= len(textdiff.splitlines()) <= 38

    assert 'added       /usr/share/mc/syntax/yaml.syntax' in textdiff


def test_exclude():
    oldpkg = get_tested_path('binary/mc-4.8.15-10.3.1.x86_64.rpm')
    newpkg = get_tested_path('binary/mc-4.8.21-2.1.x86_64.rpm')
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


def test_directory_size_and_digest_not_reported():
    # directories carry no meaningful size or content digest,
    # so S/5 changes must not be reported for them (#83)
    # NOTE: Rpmdiff.__init__ permanently disables ignored entries in the
    # class-level __FILEIDX, so restore size/digest in case the tests
    # above disabled them via ignore
    for code, name in (('S', 'size'), ('5', 'digest')):
        entry = next(e for e in Rpmdiff._Rpmdiff__FILEIDX if e[0] == code)
        entry[1] = name
    oldpkg = get_tested_path('binary/mc-4.8.15-10.3.1.x86_64.rpm')
    newpkg = get_tested_path('binary/mc-4.8.21-2.1.x86_64.rpm')
    diff = Rpmdiff(oldpkg, newpkg, ['T'])
    textdiff = diff.textdiff()
    dirs = ('/etc/mc', '/usr/lib/mc', '/usr/lib/mc/ext.d', '/usr/share/mc',
            '/usr/share/mc/help', '/usr/share/mc/skins', '/usr/share/mc/syntax')
    for line in textdiff.splitlines():
        code, path = line.split(None, 1)
        if path in dirs:
            # 'S' is the first and '5' the third slot of the diff format
            assert code[0] == '.', f'unexpected size change for directory {line}'
            assert code[2] == '.', f'unexpected digest change for directory {line}'
    # control: regular files with changed size still report S and 5
    assert 'S.5........ /etc/mc/filehighlight.ini' in textdiff
