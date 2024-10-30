# import os

# from symbols_db import logger
# from symbols_db.utils import HOME_DIRECTORY


# def from_purl_to_rust_srcname(purl):
#     return purl.replace("@", "-").split("/")[1]


# def get_all_index_names():
#     return os.listdir(f"{HOME_DIRECTORY}/.cargo/registry/src")


# def get_path_names_from_index_names(index_names):
#     # TODO: give the user the ability to specify HOME_DIRECTORY
#     return [
#         os.path.join(f"{HOME_DIRECTORY}/.cargo/registry/src", index_name)
#         for index_name in index_names
#     ]
