import sys
import os

# config your working folder and the correponding folder
# WORK_DIR = '/data1/baolingfeng/SZZ'
WORK_DIR = '/home/vietl/do28_scratch/vietl/V-SZZ/ICSE2022ReplicationPackage'

# REPOS_DIR = '/data1/baolingfeng/repos'
REPOS_DIR = '/home/vietl/do28_scratch/vietl/V-SZZ/repos'

DATA_FOLDER = os.path.join(WORK_DIR, 'data')

SZZ_FOLDER = os.path.join(WORK_DIR, 'icse2021-szz-replication-package')

DEFAULT_MAX_CHANGE_SIZE = sys.maxsize

AST_MAP_PATH = os.path.join(WORK_DIR, 'ASTMapEval_jar')

LOG_DIR = os.path.join(WORK_DIR, 'GitLogs')