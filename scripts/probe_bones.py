import json
import unreal as ue
levels = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
levels.load_level("/Game/Shot/L_Shot")
hero = {a.get_actor_label(): a for a in actors.get_all_level_actors()}["Hero"]
smc = hero.get_component_by_class(ue.SkeletalMeshComponent)
out = {}
names = [str(n) for n in smc.get_all_socket_names()]
out["total"] = len(names)
out["hands"] = [n for n in names if "hand" in n.lower()]
out["arms"] = [n for n in names if any(k in n.lower() for k in ("lowerarm", "upperarm", "index_01"))][:8]
for probe in ["hand_r", "hand_l", "ik_hand_r"]:
    out[probe] = bool(smc.does_socket_exist(probe))
try:
    loc = smc.get_socket_location("hand_r")
    out["hand_r_location"] = [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)]
except Exception as e:
    out["loc_err"] = str(e)
with open("/tmp/ue_bones.json", "w") as f:
    json.dump(out, f, indent=1)
