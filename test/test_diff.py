from rpmlint.rpmdiff import Rpmdiff

from Testing import testpath


def test_distribution_tags():
    oldpkg = testpath() / 'binary/mc-4.8.15-10.3.1.x86_64.rpm'
    newpkg = testpath() / 'binary/mc-4.8.21-2.1.x86_64.rpm'
    ignore = []
    diff = Rpmdiff(oldpkg, newpkg, ignore)
    textdiff = diff.textdiff()
    print(textdiff)
    # the count always reports one less
    assert 231 <= len(textdiff.splitlines()) <= 233

    ignore.append('T')
    ignore.append('5')
    ignore.append('S')
    diff = Rpmdiff(oldpkg, newpkg, ignore)
    textdiff = diff.textdiff()
    print('----\n' + textdiff)
    assert 36 <= len(textdiff.splitlines()) <= 38

    assert 'added       /usr/share/mc/syntax/yaml.syntax' in textdiff


def test_exclude():
    oldpkg = testpath() / 'binary/mc-4.8.15-10.3.1.x86_64.rpm'
    newpkg = testpath() / 'binary/mc-4.8.21-2.1.x86_64.rpm'
    ignore = list('T5S')

    print(Rpmdiff(oldpkg, newpkg, ignore=ignore).textdiff())

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
