"""Entry to Zeno. Parses TOML file, starts server, and runs the pipeline."""

import os
import shutil
import sys
from pathlib import Path
from typing import Union

import pkg_resources
import requests
import tomli
import uvicorn
from multiprocess import Process  # type: ignore

from zeno.api import ZenoParameters
from zeno.backend import ZenoBackend
from zeno.server import get_server
from zeno.setup import setup_zeno
from zeno.util import is_notebook, VIEW_MAP_URL, VIEWS_MAP_JSON

# Global variable to hold the Zeno server process.
# This is used to kill the server when re-running in a notebook.
ZENO_SERVER_PROCESS = None


def command_line():
    if len(sys.argv) == 1 or sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print(
            "\n \033[1mZeno\033[0m",
            pkg_resources.get_distribution("zenoml").version,
            " - Machine learning evaluation framework.",
            "\n\n",
            "\033[1mUSAGE \033[0m \n\t",
            "zeno [-h] [-v] <config.toml>",
            "\n\n",
            "\033[1mARGUMENTS \033[0m \n\t",
            "<config.toml>\t\tZeno configuration file.\n\n"
            "\033[1m GLOBAL OPTIONS \033[0m \n\t",
            "-h (--help)\t\tDisplay this help message.\n"
            "\t -v (--version)\t\tDisplay this application version.\n",
        )

        sys.exit(0)

    if len(sys.argv) != 2:
        print(
            "ERROR: Zeno take one argument, either a configuration TOML file"
            + " or the keyword 'init'. "
            + "{0} arguments were passed.",
            len(sys.argv),
        )
        sys.exit(1)

    if sys.argv[1] == "-v" or sys.argv[1] == "--version":
        print(pkg_resources.get_distribution("zenoml").version)
        sys.exit(0)

    if sys.argv[1] == "init" or sys.argv[1] == "i":
        setup_zeno()
    else:
        args = {}
        try:
            with open(sys.argv[1], "rb") as f:
                args = tomli.load(f)
        except Exception:
            print("ERROR: Failed to read TOML configuration file.")
            sys.exit(1)

        # Change working directory to the directory of the config file.
        os.chdir(os.path.dirname(os.path.abspath(sys.argv[1])))

        if "metadata" not in args:
            print(
                "ERROR: Must have 'metadata' entry which must be a CSV or Parquet file."
            )
            sys.exit(1)

        zeno(ZenoParameters(**args))


def parse_args(args: ZenoParameters) -> ZenoParameters:

    if type(args) == dict:
        args = ZenoParameters.parse_obj(args)

    if args.cache_path == "":
        args.cache_path = "./.zeno_cache/"
    else:
        args.cache_path = args.cache_path

    os.makedirs(args.cache_path, exist_ok=True)

    # Try to get view from GitHub List, if not try to read from path and copy it.
    if args.view != "":
        view_dest_path = Path(os.path.join(args.cache_path, "view.mjs"))
        view_path = Path(args.view)
        if view_path.is_file():
            if view_dest_path.is_file():
                os.remove(view_dest_path)
            shutil.copyfile(view_path, view_dest_path)
        else:
            try:
                views_res = requests.get(VIEW_MAP_URL + VIEWS_MAP_JSON)
                views = views_res.json()
                url = VIEW_MAP_URL + views[args.view]
                with open(view_dest_path, "wb") as out_file:
                    content = requests.get(url, stream=True).content
                    out_file.write(content)
            except KeyError:
                print(
                    "ERROR: View not found in list or relative path."
                    " See available views at ",
                    "https://github.com/zeno-ml/instance-views/blob/main/views.json",
                )
                sys.exit(1)

    if args.id_column == "":
        print(
            "WARNING: no id_column specified, using index as id_column. If you are",
            "using a data_column, suggest using it as id_column.",
        )

    return args


def run_zeno(args: ZenoParameters):
    zeno = ZenoBackend(args)
    app = get_server(zeno)
    zeno.start_processing()

    print("\n\033[1mZeno\033[0m running on http://{}:{}\n".format(args.host, args.port))
    uvicorn.run(app, host=args.host, port=args.port, log_level="error")


def zeno(args: Union[ZenoParameters, dict]):
    if isinstance(args, dict):
        args = ZenoParameters.parse_obj(args)
    args = parse_args(args)

    if args.serve:
        global ZENO_SERVER_PROCESS
        if ZENO_SERVER_PROCESS is not None:
            ZENO_SERVER_PROCESS.terminate()

        ZENO_SERVER_PROCESS = Process(target=run_zeno, args=(args,))
        ZENO_SERVER_PROCESS.start()

        if not is_notebook():
            ZENO_SERVER_PROCESS.join()

    else:
        zeno = ZenoBackend(args)
        return zeno
