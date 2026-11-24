import json
import unreal as ue
out = {}
out["time_unit_enums"] = sorted(n for n in dir(ue) if "TimeUnit" in n)
ch = ue.MovieSceneScriptingDoubleChannel
out["add_key_doc"] = (ch.add_key.__doc__ or "")[:600]
out["channel_methods"] = sorted(m for m in dir(ch) if not m.startswith("_"))[:25]
if hasattr(ue, "MovieSceneTimeUnit"):
    out["MovieSceneTimeUnit"] = sorted(v for v in dir(ue.MovieSceneTimeUnit) if not v.startswith("_"))
out["key_interp"] = sorted(v for v in dir(ue.MovieSceneKeyInterpolation) if not v.startswith("_")) if hasattr(ue, "MovieSceneKeyInterpolation") else None
with open("/tmp/ue_probe4.json", "w") as f:
    json.dump(out, f, indent=1)
