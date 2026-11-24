import json
import unreal as ue
out = {}
out["has_variant"] = hasattr(ue, "MovieSceneTimeWarpVariant")
if out["has_variant"]:
    v = ue.MovieSceneTimeWarpVariant()
    out["variant_methods"] = sorted(m for m in dir(v) if not m.startswith("_"))[:40]
out["params_props"] = sorted(p for p in dir(ue.MovieSceneSkeletalAnimationParams) if not p.startswith("_"))
with open("/tmp/ue_warp.json", "w") as f:
    json.dump(out, f, indent=1)
