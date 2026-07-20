# Getting set up with Python and RockmagPy

The rock magnetic data you collect during the Summer School will be analyzed using [RockmagPy](https://pmagpy.github.io/RockmagPy-notebooks) — a set of Python tools (part of the [PmagPy](https://github.com/PmagPy/PmagPy) package) with accompanying Jupyter notebooks for visualizing and interpreting the measurements. This page walks through setting up everything you need on your own computer, starting from scratch. No prior experience with Python — or with a "terminal" or "command line" — is assumed.

The whole setup takes about 15–20 minutes with a decent internet connection, and you only have to do it once. After that, getting back to work is three short commands (see [Coming back later](#coming-back-later)).

:::{note} What you are installing
:class: dropdown

- **Miniforge** — a free installer that puts Python on your computer along with `conda`, a tool for managing Python packages. It installs into your own user folder and doesn't require administrator access or interfere with anything else on your computer.
- **A conda "environment"** — a self-contained workspace named `rockmag` holding a specific Python version and the packages we need. If anything ever goes wrong inside it, you can delete it and rebuild it in minutes without touching the rest of your computer.
- **JupyterLab** — the program (it runs in your web browser) where you'll open and run notebooks. A Jupyter notebook is a document that mixes explanatory text, runnable code, and the plots that code produces.
- **PmagPy** — the Python package that contains the `rockmag` module with the functions for analyzing rock magnetic data.
- **The RockmagPy notebooks** — a folder of ready-made notebooks from the [RockmagPy-notebooks repository](https://github.com/PmagPy/RockmagPy-notebooks) for working with hysteresis, thermomagnetic, low-temperature (MPMS), and other data types.
:::

## Step 1 — Install Miniforge

Miniforge is the recommended way to get Python for scientific work. The steps differ between Mac and Windows, so follow the tab for your computer.

::::{tab-set}
:::{tab-item} Mac
:sync: mac

On a Mac, Miniforge is installed by pasting two commands into the **Terminal** app. The Terminal is a program, included on every Mac, where you type text commands instead of clicking buttons — you'll use it a few times in this guide, always by copying and pasting commands from this page.

1. Open the Terminal: press <kbd>⌘ command</kbd>+<kbd>space</kbd> to open Spotlight search, type `terminal`, and press <kbd>return</kbd>. A window opens with a blinking cursor — that's where commands go.
2. Copy the line below (select it and press <kbd>⌘ command</kbd>+<kbd>C</kbd>, or use the copy button in the corner of the box), click in the Terminal window, paste it (<kbd>⌘ command</kbd>+<kbd>V</kbd>), and press <kbd>return</kbd>. This downloads the installer (it automatically picks the right version for your Mac's chip):

   ```bash
   curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
   ```

3. When the download finishes and the prompt returns, paste this line and press <kbd>return</kbd> to run the installer:

   ```bash
   bash Miniforge3-$(uname)-$(uname -m).sh
   ```

4. The installer asks a few questions in the Terminal:
   - Press <kbd>return</kbd> to start, then press <kbd>space</kbd> to page through the license, and type `yes` and press <kbd>return</kbd> to accept it.
   - Press <kbd>return</kbd> to accept the default install location.
   - When asked *"Do you wish to update your shell profile to automatically initialize conda?"*, type `yes` and press <kbd>return</kbd>. **This one matters** — the default is "no", and answering "no" means later commands won't be found.
5. Quit the Terminal completely (<kbd>⌘ command</kbd>+<kbd>Q</kbd>) and open it again. You should now see `(base)` at the start of the command line — that's how you know the install worked.
:::

:::{tab-item} Windows (PC)
:sync: windows

On Windows, Miniforge has a point-and-click installer, and afterwards you'll use a program it installs called the **Miniforge Prompt** — a window where you type text commands instead of clicking buttons. You'll use it a few times in this guide, always by copying and pasting commands from this page.

1. Download the Windows installer from the conda-forge download page: [conda-forge.org/download](https://conda-forge.org/download/) — click the **Windows x86_64** button and save the `.exe` file.
2. Double-click the downloaded `Miniforge3-Windows-x86_64.exe` file to run it. If Windows shows a blue *"Windows protected your PC"* screen, click **More info** and then **Run anyway** — this appears for many legitimate open-source installers.
3. Click through the installer accepting the defaults: **Next**, **I Agree**, install for **Just Me**, default install location, and the pre-checked options on the final screen are fine. Click **Install**, then **Finish**.
4. Open the Start menu, type `miniforge`, and open **Miniforge Prompt**. A window opens showing `(base)` at the start of the line — that's how you know the install worked.

Whenever this guide says to type a command, it goes in the **Miniforge Prompt** — not in "Command Prompt" or "PowerShell", which won't know where Python is. To paste into the Miniforge Prompt, right-click in the window or press <kbd>ctrl</kbd>+<kbd>V</kbd>.
:::
::::

## Step 2 — Create the environment and install the software

These commands are the same on Mac and Windows. Type them in the Terminal (Mac) or the Miniforge Prompt (Windows), one at a time, pressing <kbd>return</kbd>/<kbd>enter</kbd> after each and waiting for it to finish before the next. A command is finished when the `(base)` or `(rockmag)` prompt reappears and the cursor is waiting for input again.

First, create the `rockmag` environment with Python, JupyterLab, and the plotting packages the notebooks use. This downloads a few hundred megabytes and can take several minutes; when asked to confirm, type `y` and press <kbd>return</kbd>:

```bash
conda create -n rockmag python=3.12 jupyterlab ipywidgets ipympl bokeh statsmodels dynesty
```

Next, switch into the new environment. The `(base)` at the start of the line changes to `(rockmag)`, which tells you the environment is active:

```bash
conda activate rockmag
```

Finally, install PmagPy (which includes RockmagPy) into the environment using `pip`, Python's package installer:

```bash
pip install pmagpy
```

That's the software done. You can check that it worked by copying this line into the terminal and pressing <kbd>return</kbd> — it should print a version number (like `pmagpy-4.3.16`) rather than an error:

```bash
python -c "from pmagpy import pmag; print(pmag.get_version())"
```

:::{tip}
RockmagPy is under active development, and updated versions may be released during the Summer School. To update at any point, activate the environment and run `pip install --upgrade pmagpy`.
:::

## Step 3 — Download the RockmagPy notebooks

The notebooks live in a repository (a shared folder of files) on GitHub. You don't need a GitHub account — you can download the whole thing as a ZIP file:

1. Go to [github.com/PmagPy/RockmagPy-notebooks](https://github.com/PmagPy/RockmagPy-notebooks).
2. Click the green **<> Code** button near the top right, then click **Download ZIP**.
3. Unzip the downloaded file:

::::{tab-set}
:::{tab-item} Mac
:sync: mac
Find `RockmagPy-notebooks-main.zip` in your **Downloads** folder and double-click it. A folder named `RockmagPy-notebooks-main` appears next to it. Drag that folder into your **Documents** folder so it's easy to find later.
:::
:::{tab-item} Windows (PC)
:sync: windows
Find `RockmagPy-notebooks-main.zip` in your **Downloads** folder, right-click it, and choose **Extract All…**, then **Extract**. A folder named `RockmagPy-notebooks-main` appears. Move it into your **Documents** folder so it's easy to find later.
:::
::::

:::{note}
Inside the folder you'll see a notebook called `rockmag_set_up.ipynb`. That notebook is for running RockmagPy on a JupyterHub cloud server, which we are **not** using — you can ignore it. This page replaces it for our local setup.
:::

## Step 4 — Launch JupyterLab and open a notebook

With the environment active (you see `(rockmag)` at the start of the line — if not, run `conda activate rockmag` first), start JupyterLab:

```bash
jupyter lab
```

After a few seconds your web browser opens a JupyterLab tab. (Although it runs in the browser, everything is happening locally on your computer — no internet is needed once it's running.)

In the left sidebar of JupyterLab is a file browser showing the folders on your computer. Double-click **Documents**, then **RockmagPy-notebooks-main**, then the folder for the data type you're working with (for example `hysteresis_backfield_notebooks` or `MPMS_notebooks`), and double-click a notebook (a file ending in `.ipynb`) to open it. If a dialog pops up asking you to select a kernel (some notebooks were last saved on a different system), choose **Python 3 (ipykernel)** and click **Select**. Run a notebook's cells one at a time with <kbd>shift</kbd>+<kbd>return</kbd>, or run everything via the menu with **Run → Run All Cells**.

Two things to know while JupyterLab is running:

- Keep the Terminal / Miniforge Prompt window open in the background — it's what's actually running JupyterLab. Closing it shuts JupyterLab down.
- When you're done working, save your notebook, close the browser tab, and then in the Terminal / Miniforge Prompt press <kbd>ctrl</kbd>+<kbd>C</kbd> to shut JupyterLab down (confirm with `y` if asked), or just close the window.

(coming-back-later)=
## Coming back later

Everything above is one-time setup. From now on, getting back to work is:

1. Open the Terminal (Mac) or Miniforge Prompt (Windows).
2. `conda activate rockmag`
3. `jupyter lab`

## If something goes wrong

- **`conda: command not found` (Mac)** — either the Terminal window predates the install (quit and reopen Terminal), or the installer's *"initialize conda"* question was answered "no". To fix the latter, run `~/miniforge3/bin/conda init` in the Terminal, then quit and reopen it.
- **`conda` is not recognized (Windows)** — you're typing into Command Prompt or PowerShell instead of the **Miniforge Prompt**. Open the Start menu, type `miniforge`, and use Miniforge Prompt.
- **`ModuleNotFoundError: No module named 'pmagpy'` when running a notebook** — JupyterLab was started without the environment active. Shut it down, run `conda activate rockmag`, and start `jupyter lab` again.
- **The browser doesn't open when you run `jupyter lab`** — look in the Terminal / Miniforge Prompt output for a line starting with `http://localhost:8888/lab?token=...` and copy that whole address into your browser.
- **Interactive plots or widgets don't appear** — use the menu **Kernel → Restart Kernel and Run All Cells** to rerun the notebook from a clean start; if that doesn't fix it, make sure the environment was created with the full command in Step 2 (it includes `ipywidgets` and `bokeh`).
- **Still stuck?** — bring your laptop to the instructors; a setup problem is usually a two-minute fix in person.
