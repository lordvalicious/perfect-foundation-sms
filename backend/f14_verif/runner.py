# -*- coding: utf-8 -*-
import io, os, subprocess
D   = r"C:\Users\Ryuk\Documents\perfect-foundation-sms\backend\f14_verif"
LOG = os.path.join(D, "run.log")
venv= r"C:\Users\Ryuk\Documents\perfect-foundation-sms\backend\.venv\Scripts\python.exe"
cwd = r"C:\Users\Ryuk\Documents\perfect-foundation-sms\backend"
lines=[]
try:
    r = subprocess.run([venv,"manage.py","test","apps.core.test_migrations","--verbosity=1","--noinput"], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=480)
    txt = r.stdout.decode("utf-8","replace")
    lines.append("RUN_EXIT=%d" % r.returncode)
    lines.append(txt[-1800:])
except subprocess.TimeoutExpired as e:
    lines.append("RUN_TIMEOUT")
    lines.append((e.stdout or b"").decode("utf-8","replace")[-1800:])
except Exception as ex:
    lines.append("RUN_EXC %r" % (ex,))
io.open(LOG,"w",encoding="utf-8",newline="").write("\n".join(lines))
print("WROTE_LOG_OK")
