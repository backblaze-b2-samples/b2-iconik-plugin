import os

def pytest_generate_tests(metafunc):
	os.environ['ICONIK_ID'] = 'ICONIK_ID'
	os.environ['FORMAT_NAME'] = 'ORIGINAL'
	os.environ['STORAGE_NAME'] = 'MyStorage'