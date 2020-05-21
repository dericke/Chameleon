import json
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from uuid import uuid4 as uuid
from zipfile import ZipFile

import oyaml as yaml
import pandas as pd
from flask import (
    Flask,
    render_template,
    request,
    safe_join,
    send_file,
    send_from_directory,
)

from chameleon import core

app = Flask(__name__)

RESOURCES_DIR = Path()
BASE_DIR = Path("chameleon/flask/files") / str(uuid())
BASE_DIR.mkdir(exist_ok=True)

error_list = []
extra_columns = Path("resources/extracolumns.yaml")


@app.route("/about/")
def about():
    return render_template("about.html")


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/result/", methods=["POST"])
def result():
    # country: str = request.form["country"]
    # startdate: datetime = request.form["startdate"]
    # enddate: datetime = request.form["enddate"]
    oldfile = request.files["old"]
    newfile = request.files["new"]
    output: str = "chameleon"
    if request.form.get("output"):
        output = request.form["output"]
    grouping = bool(request.form.get("grouping", False))
    modes = set(request.form.getlist("modes"))
    if not modes:  # Should only happen if client-side validation slips up
        return
    file_format: str = request.form["file_format"]

    output = Path(output).name

    cdf_set = core.ChameleonDataFrameSet(oldfile.stream, newfile.stream)
    cdf_set.separate_special_dfs()

    for mode in modes:
        try:
            result = core.ChameleonDataFrame(
                cdf_set.source_data, mode=mode, grouping=grouping
            ).query_cdf()
        except KeyError:
            error_list.append(mode)
            continue
        cdf_set.add(result)

    file_name = write_output[file_format](cdf_set, output)
    # return send_from_directory(
    #     str(BASE_DIR),
    #     file_name,
    #     as_attachment=True,
    #     mimetype=mimetype[file_format],
    # )
    the_path = (BASE_DIR / file_name).resolve()
    return send_file(
        the_path, as_attachment=True, mimetype=mimetype[file_format],
    )


def high_deletions_checker(cdf_set) -> bool:
    deletion_percentage = (
        len(cdf_set.source_data[cdf_set.source_data["action"] == "deleted"])
        / len(cdf_set.source_data)
    ) * 100
    return deletion_percentage > 20 and not user_confirm(
        "There is an unusually high proportion of deletions "
        f"({round(deletion_percentage,2)}%). "
        "This often indicates that the two input files have different scope. "
        "Would you like to continue?"
    )


def load_extra_columns() -> dict:
    try:
        with (RESOURCES_DIR / "extracolumns.yaml").open("r") as f:
            extra_columns = yaml.safe_load(f.read())
    except OSError:
        extra_columns = {"notes": None}
    return extra_columns


def user_confirm(message: str) -> bool:
    # TODO Prompt the user to continue in case of abnormally high deletion rate
    return True


def write_csv(dataframe_set, output):
    zip_name = f"{output}.zip"
    zip_path = Path(safe_join(BASE_DIR, zip_name)).resolve()

    with ZipFile(zip_path, "w") as myzip, TemporaryDirectory() as tempdir:
        for result in dataframe_set:
            file_name = f"{output}_{result.chameleon_mode}.csv"
            temp_path = Path(tempdir) / file_name
            with temp_path.open("w") as output_file:
                result.to_csv(output_file, sep="\t", index=True)
            myzip.write(temp_path, arcname=file_name)

    return zip_name


def write_excel(dataframe_set, output):
    file_name = f"{output}.xlsx"
    file_path = Path(safe_join(BASE_DIR, file_name)).resolve()

    dataframe_set.write_excel(file_path)

    return file_name


def write_geojson(dataframe_set, output):
    timeout = 120
    try:
        response = dataframe_set.to_geojson(timeout=timeout)
    except TimeoutError:
        # TODO Inform user about error
        return

    file_name = f"{output}.geojson"
    file_path = Path(safe_join(BASE_DIR, file_name)).resolve()

    with file_path.open("w") as output_file:
        json.dump(response, output_file)

    return file_name


write_output = {
    "csv": write_csv,
    "excel": write_excel,
    "geojson": write_geojson,
}

mimetype = {
    # "csv": "text/csv",
    "csv": "application/zip",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "geojson": "application/vnd.geo+json",
}
