from Testing import get_tested_mock_package

FHS = get_tested_mock_package(
files={
'/usr/dummy': {'content': ''},
'/var/dummy': {'content': ''},
'/var/local': {'content': ''}})
