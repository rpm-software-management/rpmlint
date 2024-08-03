from Testing import get_tested_mock_package

MixedOwnership = get_tested_mock_package(
files={
'/usr/bin/noproblem': {},
    '/var/lib/badfolder': {
        'metadata': {'user': 'nobody'},
        'is_dir': True},
    '/var/lib/badfolder/broken1': {
        'metadata': {'user': 'root'}},
    '/var/lib/badfolder/correctperms': {
        'metadata': {'user': 'root'},
        'is_dir': True},
    '/var/lib/badfolder/correctperms/broken2': {},
})
