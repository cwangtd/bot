import logging
import os
from functools import lru_cache

from app.settings import Settings

logger = logging.getLogger('main.app')
logger.info(f'Init {__file__}')


@lru_cache(maxsize=1)
def get_settings():
    """
    Retrieves the application settings.

    This function determines the workspace directory by traversing up from the current file's directory until it finds
    the 'app' directory. It then sets the `WORKSPACE` environment variable and loads the settings from the `.env` file.

    If running in the Docker container, the `.env` file is expected to be in the workspace directory. Otherwise,
    `envs/local.env` is used.

    Returns:
        Settings: An instance of the Settings class populated with values from the `.env` file.
    """
    my_dir = os.path.dirname(os.path.realpath(__file__))
    while my_dir != '/':
        if os.path.basename(my_dir) == 'app':
            break
        my_dir = os.path.dirname(my_dir)

    workspace = os.path.dirname(my_dir)
    # Used by Docker
    env_path = os.path.join(workspace, '.env')
    # Local development could embed the values in envs/dev.local.env
    # Run 'git update-index --assume-unchanged envs/dev.local.env' to avoid accidental commits
    # Refer to the comments in envs/dev.local.env for more details
    if not os.path.exists(env_path):
        env_path = os.path.join(workspace, 'envs/local.env')

    os.environ['WORKSPACE'] = workspace
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f'{workspace}/app/resources/secrets/gcp-secret.json'
    return Settings(_env_file=env_path)
