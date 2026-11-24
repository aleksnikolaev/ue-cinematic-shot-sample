import json
import unreal as ue

out = {}
AL = ue.EditorAssetLibrary
anim = AL.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_ChargedAttack")
out["anim"] = {
    "class": type(anim).__name__,
    "length": float(anim.get_editor_property("sequence_length")) if hasattr(anim, "get_editor_property") else None,
}
try:
    out["anim"]["rate_scale"] = float(anim.get_editor_property("rate_scale"))
except Exception as e:
    out["anim"]["rate_scale_err"] = str(e)
notifies = []
try:
    for n in anim.get_editor_property("notifies"):
        notifies.append({"time": float(n.get_editor_property("trigger_time")), "name": str(n.get_editor_property("notify_name"))})
except Exception as e:
    notifies = ["err: " + str(e)]
out["anim"]["notifies"] = notifies

reg = ue.AssetRegistryHelpers.get_asset_registry()
out["prototyping"] = sorted(str(a.asset_name) for a in reg.get_assets_by_path("/Game/LevelPrototyping", recursive=True))[:40]
out["attacks"] = {}
for nm in ["MM_Attack_01", "MM_Attack_02", "MM_Attack_03", "MM_ChargedAttack"]:
    a = AL.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/Attack/" + nm)
    if a:
        out["attacks"][nm] = round(float(a.get_editor_property("sequence_length")), 3)
with open("/tmp/ue_probe2.json", "w") as f:
    json.dump(out, f, indent=1)
