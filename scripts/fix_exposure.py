import json
import unreal as ue
levels = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
levels.load_level("/Game/Shot/L_Shot")
cam = {a.get_actor_label(): a for a in actors.get_all_level_actors()}["ShotCam"]
cc = cam.get_component_by_class(ue.CineCameraComponent)
pp = cc.get_editor_property("post_process_settings")
vals = {"auto_exposure_method": ue.AutoExposureMethod.AEM_MANUAL,
        "auto_exposure_apply_physical_camera_exposure": False,
        "auto_exposure_bias": -0.28, "bloom_intensity": 0.45, "motion_blur_amount": 0.0}
for k, v in vals.items():
    pp.set_editor_property("override_" + k, True)
    pp.set_editor_property(k, v)
cc.set_editor_property("post_process_settings", pp)
levels.save_current_level()
with open("/tmp/ue_fix.json", "w") as f:
    json.dump({"ok": True, "bias": -0.28, "physical": False}, f)
