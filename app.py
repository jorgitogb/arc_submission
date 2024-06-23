import gitlab
import yaml
from git import Repo
import os
from arctrl.arc import ARC
from arctrl.Contract.contract import Contract, DTO
from fsspreadsheet.xlsx import Xlsx
from pathlib import Path
import json
import re




def read_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def create_repo_and_fetch_origin(repo_path, remote_url):
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
    arc = ARC()
    arc_root_path = f'output/{arc_name}'
    contracts = arc.GetWriteContracts()
    for contract in contracts:
        fulfill_write_contract(arc_root_path, contract)


def fulfill_write_contract(basePath: str, contract: Contract):
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
        if contract.DTO == None:
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
    config = read_config('.config.yml')
    gl = gitlab.Gitlab(config['gitlab']['url'],
                       private_token=config['gitlab']['private_token'])
    for id in projects_id:
        project = gl.projects.get(id)
        project.delete()
        print(f"Repository with ID {id} has been removed.")


def delete_all_projects():
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

