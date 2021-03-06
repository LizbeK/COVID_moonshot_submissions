# Matt Robinson, matthew.robinson@postera.ai
# Compile all of data for csv

# general imports
import numpy as np
import pandas as pd

from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem import AllChem

from chembl_structure_pipeline import standardizer

import requests
import sys
import os

# get parent path of file
from pathlib import Path

dir_path = Path(__file__).parent.absolute()

with open(dir_path / "CDD.env", "r") as env_file:
    env_vars_dict = dict(
        tuple(line.split("="))
        for line in [x.strip("\n") for x in env_file.readlines()]
        if not line.startswith("#")
    )

vault_num = env_vars_dict["VAULT_num"]
virtual_project_id = "12336"
synthesis_project_id = "12334"
made_project_id = "12335"

vault_token = env_vars_dict["VAULT_token"]

# Start exporting of all mols

headers = {"X-CDD-token": vault_token}
url = f"https://app.collaborativedrug.com/api/v1/vaults/{vault_num}/molecules?async=True&no_structures=True"

response = requests.get(url, headers=headers)

print("BEGINNING EXPORT")
print(response)
export_info = response.json()

export_id = export_info["id"]

# CHECK STATUS of Export
import time

status = None
seconds_waiting = 0

while status != "finished":
    headers = {"X-CDD-token": vault_token}
    url = f"https://app.collaborativedrug.com/api/v1/vaults/{vault_num}/export_progress/{export_id}"

    response = requests.get(url, headers=headers)

    print("CHECKING STATUS of EXPORT:")
    # to view the status, use:
    print(response)
    status = response.json()["status"]
    print(status)

    time.sleep(5)
    seconds_waiting += 5
    if seconds_waiting > 100:
        print("Export Never Finished")
        break

if status != "finished":
    sys.exit("EXPORT IS BROKEN")

# Get Mols in 'REAL'

headers = {"X-CDD-token": vault_token}
url = (
    f"https://app.collaborativedrug.com/api/v1/vaults/5549/exports/{export_id}"
)

print("RETRIEVING CURRENT MOLS")
response = requests.get(url, headers=headers)
print(response)
# print(response.json())

current_mols = response.json()

mol_ids = []
cdd_names = []
batch_ids = []
external_ids = []
virtual_list = []
for_synthesis_list = []
made_list = []

for mol in current_mols['objects']:
    try:
        for i in range(len(mol['batches'])):
            cdd_names.append(mol['name'])
            batch_ids.append(mol['batches'][i]['id'])
            external_ids.append(mol['batches'][i]['batch_fields']['External ID'])
            mol_ids.append(mol['id'])
            project_names = []
            for project in mol['batches'][i]['projects']:
                project_names.append(project['name']) 
            if 'Compounds_Virtual' in project_names:
                virtual_list.append(True)
            else:
                virtual_list.append(False)
            if 'Compounds_for Synthesis' in project_names:
                for_synthesis_list.append(True)
            else:
                for_synthesis_list.append(False)
            if 'Compounds_Made' in project_names:
                made_list.append(True)
            else:
                made_list.append(False)
    except Exception as e:
        print(e)
        pass

current_cdd_df = pd.DataFrame(
    {
        "external_ID": external_ids,
        "CDD_name": cdd_names,
        "molecule_ID": mol_ids,
        "batch_ID": batch_ids,
        "virtual_project": virtual_list,
        "for_synthesis_project": for_synthesis_list,
        "made_project": made_list,
    }
)
current_cdd_df.to_csv(
    dir_path / "current_vault_data" / "current_vault_data.csv", index=False
)
