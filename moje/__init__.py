import yaml
from os.path import realpath, abspath, dirname, join
from pathlib import Path

def get_config():
    # find the config file with the biggest number
    root_folder = dirname(dirname(abspath(realpath(__file__))))
    config_folder = Path(root_folder) / "config"
    files = [f.stem for f in config_folder.glob("[0-9]*yaml")]
    print(config_folder)
    if len(files) == 0:
        raise ValueError(f"Please create a config file inside {config_folder}")

    priorities = [f.split(".")[0] for f in files]
    best_idx = max(enumerate(priorities), key=lambda x: x[1])[0]
    config_file = config_folder / (files[best_idx] + ".yaml")
    
    # load the config
    with open(config_file, 'r') as ymlfile:
        config = yaml.safe_load(ymlfile)

    return config



if __name__ == "__main__":

    print(get_config())

