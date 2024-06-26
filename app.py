import json
import os
import re
from pathlib import Path

import gitlab
import yaml
from arctrl.arc import ARC
from arctrl.Contract.contract import Contract
from fsspreadsheet.xlsx import Xlsx
from git import Repo


def read_config(file_path):
    """
    Reads the contents of a YAML file and returns the configuration.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict: The configuration loaded from the YAML file.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config


def create_repo_and_fetch_origin(repo_path, remote_url):
    """
    Initializes a new Git repository at the specified `repo_path` and fetches the remote origin at the given `remote_url`.

    :param repo_path: A string representing the path to the directory where the repository will be created.
    :type repo_path: str
    :param remote_url: A string representing the URL of the remote repository to fetch from.
    :type remote_url: str
    :return: None
    """
    # Initialize a new Git repository
    repo = Repo.init(repo_path, initial_branch='main')

    # Add a remote origin
    origin = repo.create_remote('origin', remote_url)

    # Fetch from the remote origin
    origin.fetch()

    # Checkout the desired branch (e.g., 'main')
    repo.git.checkout('main')

    print('Repository created, origin fetched, and branch checked out successfully.')


def add_and_push_changes(repo_path, commit_message):
    """
    Adds and pushes changes to a local Git repository.

    Args:
        repo_path (str): The path to the local Git repository.
        commit_message (str): The message to use for the commit.

    Returns:
        None

    This function opens the local Git repository specified by `repo_path`, stages all changes, commits the changes with the provided commit message, and pushes the changes to the remote origin. It then prints a success message.
    """
    # Open the local Git repository
    repo = Repo(repo_path)

    # Stage all changes
    repo.git.add('--all')

    # Commit the changes with the provided commit message
    repo.index.commit(commit_message)

    # Push the changes to the remote origin
    origin = repo.remote(name='origin')
    origin.push()

    print('Changes added, committed, and pushed to the remote origin successfully.')


def create_gitlab_repo_arc(config, repo_name):
    """
    Create a GitLab repository based on the provided configuration and repository name.

    :param config: A dictionary containing GitLab configuration details.
    :type config: dict
    :param repo_name: A string representing the name of the repository to be created.
    :type repo_name: str
    :return: A string representing the path of the created project with namespace.
    """
    gl = gitlab.Gitlab(config['gitlab']['url'],
                       private_token=config['gitlab']['private_token'])

    # Initialize the project parameters
    project_params = {
        'name': repo_name,
        'description': f'ARC description: {repo_name}',
        'visibility': 'public',
        'initialize_with_readme': True,
        'default_branch': 'main'
    }

    # If namespace is provided, include it in the project parameters
    if 'namespace' in config['gitlab']:
        project_params['namespace_id'] = config['gitlab']['namespace_id']

    # Create the new project
    project = gl.projects.create(project_params)
    print(f'Repository created: {project.web_url}')

    return project.path_with_namespace


def main():
    """
    This function reads data from a JSON file, creates GitLab repositories, initializes local Git repositories,
    fetches the remote origin, initializes ARC, and adds and pushes changes.

    Parameters:
    None

    Returns:
    None
    """
    data_path = "data/edal.json"
    with open(data_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        for i, item in enumerate(data[:5]):
            project_folder_path = os.path.dirname(os.path.abspath(__file__))
            arc_name = re.sub(r'[^\w.+ -]', ' ', item['name'])
            print(f"Project {i+1}: {arc_name}")

            config = read_config('.config.yml')

            # Create gitlab repo
            repo_path_namespace = create_gitlab_repo_arc(config, arc_name)
            repo_path = f'{project_folder_path}/output/{repo_path_namespace}'
            remote_url = f'http://dmz-web-140:22223/{repo_path_namespace}.git'
            # Create local repo and fetch origin
            create_repo_and_fetch_origin(repo_path, remote_url)
            # Init ARC
            init_arc(repo_path_namespace)
            # Add and push changes
            add_and_push_changes(repo_path, 'Initial commit')


def init_arc(arc_name='my-arc'):
    """
    Initializes an ARC with the given name.

    Args:
        arc_name (str, optional): The name of the ARC. Defaults to 'my-arc'.

    Returns:
        None
    """
    arc = ARC()
    arc_root_path = f'output/{arc_name}'
    contracts = arc.GetWriteContracts()
    for contract in contracts:
        fulfill_write_contract(arc_root_path, contract)


def fulfill_write_contract(basePath: str, contract: Contract):
    """
    A function that fulfills a write contract based on the provided base path and contract.

    Args:
        basePath (str): The base path where the contract will be fulfilled.
        contract (Contract): The contract object containing information to fulfill.

    Returns:
        None
    """
    def ensure_directory(filePath: Path):
        if filePath.suffix or filePath.name.startswith("."):
            filePath = filePath.parent
        path_str = str(filePath)
        # Split the path into individual directories
        directories = path_str.split(os.path.sep)
        current_path = ""
        # Iterate through each directory in the path
        for directory in directories:
            # Append the current directory to the current path
            current_path = os.path.join(current_path, directory)
            # Check if the current path exists as a directory
            exists = os.path.exists(current_path)
            if not exists:
                os.makedirs(current_path)

    p = Path(basePath).joinpath(contract.Path)
    if contract.Operation == "CREATE":
        if contract.DTO is None:
            ensure_directory(p)
            Path.write_text(p, "")
        elif contract.DTOType.name == "ISA_Assay" or contract.DTOType.name == "ISA_Study" or contract.DTOType.name == "ISA_Investigation":
            ensure_directory(p)
            Xlsx.to_xlsx_file(p, contract.DTO.fields[0])
        elif contract.DTOType == "PlainText":
            ensure_directory(p)
            Path.write_text(p, contract.DTO.fields[0])
        else:
            print(
                "Warning: The given contract is not a correct ARC write contract: ", contract)


def delete_project(projects_id):
    """
    Deletes GitLab projects based on the provided project IDs.

    Args:
        projects_id (list): A list of integers representing the IDs of the projects to be deleted.

    Returns:
        None

    This function reads the configuration file '.config.yml' to retrieve the GitLab URL and private token.
    It then creates a GitLab instance using the provided URL and private token.
    It iterates over the list of project IDs and deletes each project using the GitLab instance.
    It prints a message indicating the ID of the removed project.

    Example usage:
        delete_project([1, 2, 3])
    """
    config = read_config('.config.yml')
    gl = gitlab.Gitlab(config['gitlab']['url'],
                       private_token=config['gitlab']['private_token'])
    for id in projects_id:
        project = gl.projects.get(id)
        project.delete()
        print(f"Repository with ID {id} has been removed.")


def delete_all_projects():
    """
    Deletes all projects from the GitLab instance specified in the configuration file.

    This function reads the configuration file '.config.yml' to retrieve the GitLab URL and private token.
    It then creates a GitLab instance using the provided URL and private token.
    It retrieves a list of all projects from the GitLab instance.
    For each project in the list, it deletes the project and prints a message indicating the ID of the removed project.

    This function does not take any parameters.

    This function does not return any value.
    """
    config = read_config('.config.yml')
    gl = gitlab.Gitlab(config['gitlab']['url'],
                       private_token=config['gitlab']['private_token'])
    projects = gl.projects.list()
    for project in projects:
        project.delete()
        print(f"Repository with ID {project.id} has been removed.")


if __name__ == '__main__':
    #delete_all_projects()
    main()
    # delete_project([9,11])
