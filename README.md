# GitHub Commit Parser (GHCP)

A tool that parses emails from GitHub commits.

## Features
- Extracts email information for each commit in a GitHub repository if present
- Save the results in JSON files

## Requirements
- Python 3.x
- requests

## Installation
1. Clone the repository to your local machine:
    ```
    $ git clone https://github.com/onsec-io/ghcp.git
    ```

2. Navigate to the project directory:
    ```
    $ cd ghcp
    ```

3. Install the `requests` package:
    ```
    $ pip install requests
    ```

4. Run the tool:
    ```
    python ghcp.py
    ```

## Usage
```bash
python ghcp.py
usage: ghcp.py [-h] -u USER [-t TOKEN] [-f GETFOLLOWERS] [-o OUTPUTFOLDER] [--getforked GETFORKED]
                 [--skiprepos SKIPREPOS]
ghcp.py: error: the following arguments are required: -u/--user
```

* `-u USER` — the name of the user or organization in the GitHub service is a required parameter
* `-t TOKEN` — the Github authorization token. It helps to raise the API request limit. An unauthorized user has a limit of 60 requests per minute, while an authorized user has a limit of 5000 requests per minute.
* `-f 0|1` — get additionally information about followers. In some cases, there may be other developers from the same organization. (default: 0)
* `-o OUTPUTFOLDER` — the directory name for saving output JSON files. (default: output)
* `--getforked 0|1` — the option to consider and handle forked repositories, as most of the time, users fork repositories but don't make any commits to them, and therefore there is usually nothing of interest in them. (default: 0)
* `--skiprepos 0|1` — the option to skip company repositories is useful when you only want to handle followers and members. (default: 0)

## Example

1. Specify a user or an organization name you want to parse using the `-u` parameter (e.g. [test](https://github.com/test)).
2. Specify other parameters and flags if needed
3. Run the parser
   ```
   python ghcp.py -u test
   ```
4. The results will be saved in the output folder (default: `output`) in two files: `<username>.json` and `<username>_members.json`.

## License

This project is licensed under the [GPL 3.0 License](https://github.com/onsec-io/ghcp/blob/main/LICENSE).

