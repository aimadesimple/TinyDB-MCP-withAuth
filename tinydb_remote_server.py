import os
from typing import Dict, List

import uvicorn
from tinydb import TinyDB

from auth0_mcp import Auth0Config, Auth0Mcp

auth0_mcp = Auth0Mcp("tinydb-remote-mcp", Auth0Config.from_env())
mcp = auth0_mcp.mcp
app = auth0_mcp.app()

db = TinyDB("db.json")

@mcp.tool()
def insert_data(data: dict) -> str:
    """
    Insert a single document into the database.

    Args:
        data(dict): The data to insert into the database.

    Returns:
        str: The string "Data inserted successfully"

    Example:
    ```json
    {
        "name": "John Doe",
        "age": 30
    }
    ```
    """
    db.insert(data)
    return "Data inserted successfully."

@mcp.tool()
def get_all_data() -> List[Dict]:
    """
    Get data from the database

    Args:
        None

    Returns:
        List[Dict]: The list of all data from the database
    """
    return db.all()

@mcp.tool()
def delete_all_data() -> str:
    """
    Delete data from the database

    Args:
        None

    Returns:
        str: The string "Data deleted successfully"
    """
    db.truncate()
    return "Data deleted successfully"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
