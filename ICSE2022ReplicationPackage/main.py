import os
import sys
import json
import logging as log
import subprocess
from setting import *
from tqdm.auto import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from time import sleep as original_sleep
import time

sys.path.append(os.path.join(SZZ_FOLDER, 'tools/pyszz/'))

from szz.ag_szz import AGSZZ
from szz.b_szz import BaseSZZ
from szz.l_szz import LSZZ
from szz.ma_szz import MASZZ, DetectLineMoved
from szz.r_szz import RSZZ
from szz.ra_szz import RASZZ
from szz.pd_szz import PyDrillerSZZ
from szz.my_szz import MySZZ

from data_loader import JAVA_CVE_FIX_COMMITS, C_CVE_FIX_COMMITS, JAVA_PROJECTS, C_PROJECTS, read_cve_commits, load_annotated_commits

def get_commit_hashes_between(repo_path, bic, bfc):
    """
    Get a list of commit hashes between two specified commits in a Git repository.
    The list is ordered from oldest to newest.

    :param repo_path: Path to the local Git repository.
    :param bic: The starting commit hash (older).
    :param fic: The ending commit hash (newer).
    :return: A list of commit hashes.
    """
    try:
        # Navigate to the repository directory
        os.chdir(repo_path)
        # file_path = os.path.join(repo_path, relative_file_path)
        # git log A..B has nothing to do with age of commits
        # git log A..B : Commits reachable from B but not from A.
        command = ['git', 'log', '--format=%H', f'{bfc}..{bic}']
        
        # Execute the command
        result = subprocess.run(command, cwd=repo_path, check=True, capture_output=True, text=True)
        os.chdir(WORK_DIR)
        # Split the output into lines and return as a list
        print(f"GET COMMITS BETWEEN {bic} AND {bfc}.")
        return result.stdout.strip().split('\n')[1:]
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []


def run_szz(project, commits, method, repo_url=None, max_change_size=DEFAULT_MAX_CHANGE_SIZE):
    output_file = "results/{method}-{project}.json".format(method=method, project=project)
    output_latent_file = "results/{method}-{project}-latent.json".format(method=method, project=project)
    if os.path.exists(output_file):
        return
    use_temp_dir = False
    print("Running SZZ for project:", project)

    output = {}
    output_latent = {}

    if method == "b":
        b_szz = BaseSZZ(repo_full_name=project, repo_url=repo_url, repos_dir=REPOS_DIR, use_temp_dir=use_temp_dir)
        for commit in commits:
            print('Fixing Commit:', commit)
            imp_files = b_szz.get_impacted_files(fix_commit_hash=commit, file_ext_to_parse=['c', 'java', 'cpp', 'h', 'hpp'], only_deleted_lines=True)
            bug_introducing_commits = b_szz.find_bic(fix_commit_hash=commit,
                                      impacted_files=imp_files,
                                      ignore_revs_file_path=None)
            output[commit] = [commit.hexsha for commit in bug_introducing_commits]
    elif method == "ag":
        ag_szz = AGSZZ(repo_full_name=project, repo_url=repo_url, repos_dir=REPOS_DIR, use_temp_dir=use_temp_dir)
        for commit in commits:
            print('Fixing Commit:', commit)
            imp_files = ag_szz.get_impacted_files(fix_commit_hash=commit, file_ext_to_parse=['c', 'java', 'cpp', 'h', 'hpp'], only_deleted_lines=True)
            bug_introducing_commits = ag_szz.find_bic(fix_commit_hash=commit,
                                      impacted_files=imp_files,
                                      ignore_revs_file_path=None,
                                      max_change_size=max_change_size)
            output[commit] = [commit.hexsha for commit in bug_introducing_commits]
    elif method == "ma":
        ma_szz = MASZZ(repo_full_name=project, repo_url=repo_url, repos_dir=REPOS_DIR, use_temp_dir=use_temp_dir)
        for commit in commits:
            print('Fixing Commit:', commit)
            imp_files = ma_szz.get_impacted_files(fix_commit_hash=commit, file_ext_to_parse=['c', 'java', 'cpp', 'h', 'hpp'], only_deleted_lines=True)
            bug_introducing_commits = ma_szz.find_bic(fix_commit_hash=commit,
                                      impacted_files=imp_files,
                                      ignore_revs_file_path=None,
                                      max_change_size=max_change_size)

            output[commit] = [commit.hexsha for commit in bug_introducing_commits]
    elif method == "my":
        my_szz = MySZZ(repo_full_name=project, repo_url=repo_url, repos_dir=REPOS_DIR, use_temp_dir=use_temp_dir, ast_map_path=AST_MAP_PATH)
        # print(commits[0])
        # print(my_szz)
        for commit in tqdm(commits, desc="BUG FIXING COMMIT", leave=True):
            # print('Fixing Commit:', commit)
            # imp_files = my_szz.get_impacted_files(fix_commit_hash=commit, file_ext_to_parse=['c', 'java', 'cpp', 'h', 'hpp'], only_deleted_lines=True)
            imp_files = my_szz.get_impacted_files(fix_commit_hash=commit, file_ext_to_parse=['c', 'cpp', 'h', 'hpp', 'cxx', 'hxx', 'cc', 'hh'], only_deleted_lines=True)
            bug_introducing_commits = my_szz.find_bic(fix_commit_hash=commit,
                                      impacted_files=imp_files,
                                      ignore_revs_file_path=None)
            # print(bug_introducing_commits[0])
            # exit(-1)
            # {
            #     'line_num': 6056, 
            #     'line_str': 'Js::RegSlot rhsLocation,', 
            #     'file_path': 'lib/Runtime/ByteCode/ByteCodeEmitter.cpp', 
            #     'previous_commits': 
            #     [
            #         (
            #             '5d8406741f8c60e7bf0a06e4fb71a5cf7a6458dc', 
            #             6056, 
            #             'Js::RegSlot rhsLocation,'
            #         )
            #     ]
            # }
            if len(bug_introducing_commits) > 0:
                output[commit] = bug_introducing_commits
                # latent_data = []
                # for bic in bug_introducing_commits:
                #     # print("BIC: \n", type(bic['previous_commits'][0]))
                #     for bic_commit in bic['previous_commits']:
                #         print("BIC commit before latent ",bic_commit)
                #         latent_commits = get_commit_hashes_between(os.path.join(REPOS_DIR, project), bic=bic_commit[0], bfc=commit)
                #         print(fr"GET {len(latent_commits)} latent commits")
                #         if len(latent_commits) > 0:
                #             for latent_commit in tqdm(latent_commits, desc=f"Latent commits for BFC={commit} and BIC={bic_commit[0]}\n", leave=False):
                #                 latent_imp_files = my_szz.get_impacted_files(fix_commit_hash=latent_commit, file_ext_to_parse=['c', 'cpp', 'h', 'hpp', 'cxx', 'hxx', 'cc', 'hh'], only_deleted_lines=True)
                #                 latent_bug_introducing_commits = my_szz.find_bic(fix_commit_hash=latent_commit,
                #                         impacted_files=latent_imp_files,
                #                         ignore_revs_file_path=None)
                #                 print(fr"GET {len(latent_bug_introducing_commits)} latent bug introd    ucing commits")
                #                 if len(latent_bug_introducing_commits) > 0:
                #                     for latent_bic in latent_bug_introducing_commits:
                #                         print("latent bug introducing commit: \n",latent_bic)
                #                         # exit()
                #                         if len(latent_bic['previous_commits']) > 0:
                #                             for latent_bic_info in latent_bic['previous_commits']:
                #                                 print(latent_bic_info)
                #                                 print("bug introducing commit: \n", bic_commit)
                #                                 if latent_bic_info == bic_commit:
                #                                     latent_data.append(latent_bic)
                #         output_latent[(commit,bic_commit[0])] = latent_data
                
    elif method == "ra":
        ra_szz = RASZZ(repo_full_name=project, repo_url=repo_url, repos_dir=REPOS_DIR, use_temp_dir=use_temp_dir)
        for commit in commits:
            print('Fixing Commit:', commit)
            imp_files = ra_szz.get_impacted_files(fix_commit_hash=commit, file_ext_to_parse=['c', 'java', 'cpp', 'h', 'hpp'], only_deleted_lines=True)
            bug_introducing_commits = ra_szz.find_bic(fix_commit_hash=commit,
                                      impacted_files=imp_files,
                                      ignore_revs_file_path=None,
                                      max_change_size=max_change_size)
            output[commit] = [commit.hexsha for commit in bug_introducing_commits]

    with open(output_file, 'w') as fout:
        json.dump(output, fout, indent=4)
    # with open(output_latent_file, 'w') as fout:
    #     json.dump(output_latent, fout, indent=4)


def print_thread_count():
    current_threads = threading.enumerate()
    number_of_threads = len(current_threads)
    print(f"Number of threads currently running: {number_of_threads}")

def run_szz_concurrently(projects, method, repo_url=None, max_change_size=DEFAULT_MAX_CHANGE_SIZE):
    # print_thread_count()
    with ThreadPoolExecutor(max_workers=5) as executor:
        # print_thread_count()
        # Submit all projects to the executor
        future_to_project = {executor.submit(run_szz, project, read_cve_commits(project, C_CVE_FIX_COMMITS), method, repo_url, max_change_size): project for project in projects}
        
        for future in as_completed(future_to_project):
            project = future_to_project[future]
            try:
                future.result()  # You can handle results or exceptions here
            except Exception as exc:
                print(f'{project} generated an exception: {exc}')
    original_sleep(1)
    print_thread_count()

if __name__ == "__main__":
    use_temp_dir = False

    # fixing_commits = JAVA_CVE_FIX_COMMITS
    fixing_commits = C_CVE_FIX_COMMITS

    # project_commits1 = load_annotated_commits()
    project_commits = C_PROJECTS
    
    # repo_url = 'https://github.com/WebKit/WebKit'
    repo_url = 'https://github.com/chakra-core/ChakraCore'
    start_time = time.time()
    run_szz_concurrently(project_commits, 'my', repo_url=repo_url)
    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Time taken to conduct the task: {elapsed_time} seconds")
    # for project in project_commits:
    #     print("Project:", project)
    #     # repo_url = 'https://github.com/FFmpeg/FFmpeg.git'
    #     # repo_url = 'https://github.com/chakra-core/ChakraCore'
    #     repo_url = 'https://github.com/WebKit/WebKit'
    #     fixing_cve_commits = read_cve_commits(project, fixing_commits)
    #     run_szz(project, fixing_cve_commits, 'my', repo_url = repo_url)

    #     break


        
    