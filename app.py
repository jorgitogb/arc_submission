import gitlab
import yaml


def read_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def main():
    config = read_config('.config.yml')

    gl = gitlab.Gitlab(config['gitlab']['url'],
                       private_token=config['gitlab']['private_token'])

    # Initialize the project parameters
    project_params = {
        'name': 'my-repo-from-python',
        'description': 'Your repository description from python',
        'visibility': 'public'
    }

    # If namespace is provided, include it in the project parameters
    if 'namespace' in config['gitlab']:
        project_params['namespace_id'] = config['gitlab']['namespace']

    # Create the new project
    new_project = gl.projects.create(project_params)

    print(f'Repository created: {new_project.web_url}')

def delete_project(project_id):
    config = read_config('.config.yml')
    gl = gitlab.Gitlab(config['gitlab']['url'],
                       private_token=config['gitlab']['private_token'])
    gl.projects.delete(project_id)
    print(f"Repository with ID {project_id} has been removed.")


if __name__ == '__main__':
    main()
    #delete_project(16)
