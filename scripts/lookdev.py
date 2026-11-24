import json
import unreal as ue

OUT = {"steps": [], "shots": []}
def mark(s, **kw):
    OUT["steps"].append(s); OUT.update(kw)
    with open("/tmp/ue_look.json", "w") as f:
        json.dump(OUT, f, indent=1)

levels = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
AL = ue.EditorAssetLibrary
levels.load_level("/Game/Shot/L_Shot")
by_label = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
hero = by_label["Hero"]
beam_actor = by_label["Beam"]
world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
mark("level")

# поза персонажа на моменте выпуска
smc = hero.skeletal_mesh_component
charged = AL.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_ChargedAttack")
try:
    smc.play_animation(charged, False)
    smc.set_position(1.15, False)
    mark("pose")
except Exception as e:
    mark("pose FAILED", pose_err=str(e))

# кандидаты: позиция камеры, точка интереса, фокусное
CANDIDATES = [
    ("a_over_shoulder", (-250, -150, 175), (300, 10, 120), 40.0),
    ("b_three_quarter", (-170, -330, 150), (260, 40, 115), 35.0),
    ("c_low_front",     (330, -300, 70),  (0, 0, 115),    50.0),
    ("d_side_wide",     (120, -470, 130), (120, 0, 110),  28.0),
    ("e_high_back",     (-330, -90, 290), (420, -20, 100), 35.0),
    ("f_close_side",    (60, -260, 145),  (200, -10, 120), 45.0),
]

for helper in actors.get_all_level_actors():
    if isinstance(helper, ue.SceneCapture2D):
        actors.destroy_actor(helper)

comp = beam_actor.get_component_by_class(ue.NiagaraComponent)
mark("beam component", has_asset=bool(comp.get_editor_property("asset")))
comp.set_visibility(True)
comp.set_force_solo(True)
comp.set_rendering_enabled(True)
comp.activate(True)
comp.set_component_tick_enabled(False)
mark("beam ready")

shot = actors.spawn_actor_from_class(ue.SceneCapture2D, ue.Vector(), ue.Rotator(), True)
cap = shot.get_component_by_class(ue.SceneCaptureComponent2D)
cap.set_editor_property("capture_source", ue.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_editor_property("capture_every_frame", False)
cap.set_editor_property("capture_on_movement", False)
cap.set_editor_property("always_persist_rendering_state", True)
post = cap.get_editor_property("post_process_settings")
for name, value in (("auto_exposure_method", ue.AutoExposureMethod.AEM_MANUAL),
                    ("auto_exposure_apply_physical_camera_exposure", False),
                    ("auto_exposure_bias", 0.0),
                    ("bloom_intensity", 0.5),
                    ("motion_blur_amount", 0.0)):
    post.set_editor_property("override_" + name, True)
    post.set_editor_property(name, value)
cap.set_editor_property("post_process_settings", post)
target = ue.RenderingLibrary.create_render_target2d(shot, 960, 540, ue.TextureRenderTargetFormat.RTF_RGBA8)
cap.set_editor_property("texture_target", target)
mark("capture ready")

OUTDIR = "/Users/alex/Documents/niksoft-ue-cinematic-sample/lookdev"
state = {"ticks": 0, "idx": 0, "advanced": False}

def tick(_delta):
    try:
        state["ticks"] += 1
        if state["ticks"] < 40:
            return
        if not state["advanced"]:
            # догнать симуляцию до разряда
            comp.advance_simulation(120, 1.0 / 120.0)
            state["advanced"] = True
            return
        i = state["idx"]
        if i >= len(CANDIDATES):
            ue.unregister_slate_post_tick_callback(handle)
            mark("done")
            return
        name, loc, look, fov = CANDIDATES[i]
        v = ue.Vector(*loc)
        rot = ue.MathLibrary.find_look_at_rotation(v, ue.Vector(*look))
        shot.set_actor_location_and_rotation(v, rot, False, False)
        cap.set_editor_property("fov_angle", fov)
        cap.capture_scene()
        ue.RenderingLibrary.export_render_target(world, target, OUTDIR, name + ".png")
        OUT["shots"].append(name)
        state["idx"] += 1
        mark("shot " + name)
    except Exception as e:
        mark("tick FAILED", tick_err=str(e))
        ue.unregister_slate_post_tick_callback(handle)

handle = ue.register_slate_post_tick_callback(tick)
