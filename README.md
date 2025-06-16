<h1 align="center">⏰ temps</h1>
<p align="center">A free & open-source CLI time-tracking tool that allows you to make punch-clock entries for daily work time to keep track of overtime balances including functionality for showing stats and exporting Excel timesheets.<br/>I built this very simple tool to accomodate my personal need for such a program and decided to share in case anyone else finds it useful.</p>
<div align="center">
    <a href="https://github.com/maxschroen/temps"><img src="https://img.shields.io/github/stars/maxschroen/temps" alt="Stars Badge"/></a>
    <a href="https://github.com/maxschroen/temps/network/members"><img src="https://img.shields.io/github/forks/maxschroen/temps" alt="Forks Badge"/></a>
    <a href="https://github.com/maxschroen/temps/pulls"><img src="https://img.shields.io/github/issues-pr/maxschroen/temps" alt="Pull Requests Badge"/></a>
    <a href="https://github.com/maxschroen/temps/issues"><img src="https://img.shields.io/github/issues/maxschroen/temps" alt="Issues Badge"/></a>
    <a href="https://github.com/maxschroen/temps/graphs/contributors"><img alt="GitHub contributors" src="https://img.shields.io/github/contributors/maxschroen/temps?color=2b9348"></a>
    <a href="https://github.com/maxschroen/temps/blob/main/LICENSE"><img src="https://img.shields.io/github/license/maxschroen/temps?color=2b9348" alt="License Badge"/></a>
</div>
<h4 align="center">Attributions</h4>
<p align="center"><a href="https://github.com/kazhala/InquirerPy">InquirerPy</a> - <a href="https://duckdb.org/">DuckDB</a> - <a href="https://pandas.pydata.org/">pandas</a></p>


## Contents
- [Limitations](#limitations)
- [Changelog](#changelog)
- [Requirements](#requirements)
- [Installation](#installation)
- [How To Use](#how-to-use)

## Limitations
This tool has certain limitations due to the way it was designed to accomodate my personal time-tracking needs, including the following:
- 1 entry per day (entries are timeboxed per day)
- No mixed entries (e.g. 4h work, 4h sick)
- No entries for future days
- Automatic break time deduction
- No support for previous overtime time balances
- Only 5 types of entries:
  - **Work**: Regular working day 
  - **Vacation**: Vacation / PTO days
  - **Public / Company Holiday**: Country public holidays or days like Christmas or New Years where you might get PTO from your employer
  - **Sick Leave**: PTO during sickness
  - **Overtime Compensation**: Days taken off with the accrued overtime balance

## Changelog

#### v1.0
- Initial release

<details>
  <summary>Older Versions</summary>
  <h4>No older versions available.</h4>
  <!-- <ul>
    <li>Removed Pylette dependency
      <ul>
        <li>Image color extraction implemented via K-Means-Clustering (initially seemd counterintuitive but results are of higher visual quality than those from median cut)</li>
      </ul>
    </li>
  </ul>
  <h4>v0.0</h4>
  <ul>
    <li>Initial release</li>
  </ul> -->
</details>

## Requirements
- [macOS Sequoia](https://www.apple.com/macos/macos-sequoia/) (tested for 15.X)
  - might work on other Unix-like operating systems but unconfirmed so far
- [uv](https://github.com/astral-sh/uv)

## Installation
After installing all hard [requirements](#requirements), the simplest way to get the script is to clone the repository and then install the required packages via a Python environment.

1. Clone the repository.
```bash
# Clone using web url
git clone https://github.com/maxschroen/temps.git
# OR clone using GitHub CLI
gh repo clone maxschroen/temps
# Navigate to project folder
cd temps
```

2. Install dependencies.
```bash
uv sync
```

## How To Use
To run the script, simply navigate to the root of the repository after performing the installation steps and run:

```bash
# Navigate to project directory
cd <PATH/TO/GITHUB_REPO>/temps
# Run main.py file
uv run main.py
```

The script will give you prompts to walk you through the process.

### Shortcut
In case you want to make the utility available via a one-word command, follow these instructions.

1. Create alias for application by pasting the following into your shell config (.zshrc, .bashrc, etc.)
  ```bash
  alias temps='uv run --directory=<PATH/TO/GITHUB/REPO>/temps main.py' # replace with your own path
  ```

2. Quit and reopen your shell or set the shell config active via following command:
```bash
source <YOUR_SHELL_CONFIG> # replace with your own file path e.g. ~/.zshrc or ~/.bashrc
```