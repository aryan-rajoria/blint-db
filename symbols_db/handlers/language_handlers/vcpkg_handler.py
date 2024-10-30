import os
import subprocess

from symbols_db import VCPKG_LOCATION, VCPKG_URL, VCPKG_HASH
from symbols_db.handlers.language_handlers import BaseHandler
from symbols_db.projects_compiler.vcpkg import (
    exec_explorer,
    git_checkout_vcpkg_commit,
    git_clone_vcpkg,
    run_vcpkg_install_command,
)
from symbols_db.utils.utils import subprocess_run_debug
from symbols_db.handlers.git_handler import git_checkout_commit, git_clone


class VcpkgHandler(BaseHandler):
    strip = False

    def __init__(self):
        git_clone(VCPKG_URL, VCPKG_LOCATION)
        git_checkout_commit(VCPKG_LOCATION, VCPKG_HASH)
        run_vcpkg_install_command()

    def build(self, project_name):
        inst_cmd = f"./vcpkg install {project_name}".split(" ")
        inst_run = subprocess.run(inst_cmd, cwd=VCPKG_LOCATION, capture_output=True)
        subprocess_run_debug(inst_run, project_name)

    def find_executables(self, project_name):
        project_path = f"{project_name}_x64-linux"
        target_directory = VCPKG_LOCATION / "packages" / project_path
        return exec_explorer(target_directory)

    def delete_project_files(self, project_name):
        pass

    def get_project_list(self):
        ports_path = VCPKG_LOCATION / "ports"
        return os.listdir(ports_path)


def get_vcpkg_projects():
    git_clone_vcpkg()
    git_checkout_vcpkg_commit()
    run_vcpkg_install_command()

    ports_path = VCPKG_LOCATION / "ports"
    return os.listdir(ports_path)


def vcpkg_build(project_name):
    inst_cmd = f"./vcpkg install {project_name}".split(" ")
    inst_run = subprocess.run(inst_cmd, cwd=VCPKG_LOCATION, capture_output=True)
    subprocess_run_debug(inst_run, project_name)


def archive_explorer(directory):
    """
    Walks through a directory and identifies executable files using the `file` command.

    Args:
      directory: The directory to search.

    Returns:
      A list of executable file paths.
    """
    executables = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                result = subprocess.run(["file", file_path], capture_output=True)
                if b"archive" in result.stdout:
                    executables.append(file_path)
            # FileNotFoundError may be correct as `file` command executable is a file
            except FileNotFoundError:
                print(
                    "Error: 'file' command not found. Make sure it's installed and in your PATH."
                )
                return []
    return executables


def find_vcpkg_executables(project_name):
    project_path = f"{project_name}_x64-linux"
    target_directory = VCPKG_LOCATION / "packages" / project_path
    return exec_explorer(target_directory)
