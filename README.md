Usage:
```
py -m pip install -r requirements.txt
py verify.py (Optional, if gameinfo.gi is corrupt)
py setup.py
py run-mapping.py
```

If you don't want to / don't know how to install python, you can download the executables in the release section which will do the same thing. These might get falsely flagged by Defender however, so you will need to whitelist them. I recommend just installing python and do the steps above instead.

When running this for the first time, you need to run `setup` and `verify` if you have a modified `gameinfo.gi`. After that you can just do `run-mapping` to launch cs2 hammer with CS2KZ enabled. After you quit CS2, `run-mapping` should automatically returns the gameinfo files to their original state.

Alternatively, you can use `run-listen` to run CS2KZ without mapping tools, or use `run-dedicated` (launches a CS2KZ server) and `run-insecure` to run the server and the client separately.
