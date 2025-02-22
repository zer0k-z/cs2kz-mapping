Usage:
```
pip install -r requirements.txt
py verify.py (Optional, if gameinfo.gi is corrupt)
py setup.py
py run.py
```

If you don't want to / don't know how to install python, you can download the executables in the release section which will do the same thing.

When running this for the first time, you need to run `setup` and `verify` if you have a modified `gameinfo.gi`. After that you can just do `run` to launch cs2 hammer with CS2KZ enabled. After you quit CS2, `run` should automatically returns the gameinfo files to their original state.
