import os

from rss_digest.config import AppConfig

TEST_DATA_BASE = 'test/test_data'
TEST_DIR_BASE = os.path.join(TEST_DATA_BASE, 'run')

def get_test_dir(name: str) -> str:
    test_dir = os.path.join(TEST_DIR_BASE, name)
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    return test_dir

def get_test_config(name: str) -> AppConfig:
    test_dir = get_test_dir(name)
    config_dir = os.path.join(test_dir, 'config')
    data_dir = os.path.join(test_dir, 'data')
    return AppConfig(config_dir, data_dir)