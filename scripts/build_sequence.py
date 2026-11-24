import json
import unreal as ue

SEQ_PATH = "/Game/Shot"
SEQ_NAME = "LS_Shot"
FULL = SEQ_PATH + "/" + SEQ_NAME
LEVEL = "/Game/Shot/L_Shot"
FPS = 30
DUR = 2.0
STEPS = []
INFO = {}

def mark(name, **kw):
    STEPS.append(name)
    INFO.update(kw)
    with open("/tmp/ue_seq.json", "w") as f:
        json.dump({"steps": STEPS, "info": INFO}, f, indent=1)

levels = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors_sys = ue.get_editor_subsystem(ue.EditorActorSubsystem)
AL = ue.EditorAssetLibrary
TOOLS = ue.AssetToolsHelpers.get_asset_tools()

levels.load_level(LEVEL)
mark("level")

if AL.does_asset_exist(FULL):
    AL.delete_asset(FULL)
seq = TOOLS.create_asset(SEQ_NAME, SEQ_PATH, ue.LevelSequence, ue.LevelSequenceFactoryNew())
seq.set_display_rate(ue.FrameRate(FPS, 1))
seq.set_playback_start_seconds(0.0)
seq.set_playback_end_seconds(DUR)
mark("sequence created")

by_label = {a.get_actor_label(): a for a in actors_sys.get_all_level_actors()}
INFO["labels"] = sorted(by_label.keys())
cam = by_label["ShotCam"]
hero = by_label["Hero"]
beam = by_label["Beam"]

cam_b = seq.add_possessable(cam)
hero_b = seq.add_possessable(hero)
beam_b = seq.add_possessable(beam)
mark("bindings")

# camera cut
cut_track = seq.add_track(ue.MovieSceneCameraCutTrack)
cut = cut_track.add_section()
cut.set_range_seconds(0.0, DUR)
try:
    cut.set_camera_binding_id(seq.get_binding_id(cam_b))
    mark("camera cut")
except Exception as e:
    mark("camera cut FAILED", cut_err=str(e))

# camera move: position and aim keyed over the shot
tr_track = cam_b.add_track(ue.MovieScene3DTransformTrack)
tr = tr_track.add_section()
tr.set_range_seconds(0.0, DUR)
chans = tr.get_all_channels()
INFO["transform_channels"] = len(chans)

target = ue.Vector(20, 10, 120)
moves = [
    (0.00, ue.Vector(520, -390, 128)),
    (0.70, ue.Vector(498, -374, 122)),
    (1.30, ue.Vector(480, -362, 116)),
    # толчок камеры на вспышке, четыре кадра
    (1.37, ue.Vector(474, -358, 123)),
    (1.40, ue.Vector(479, -364, 110)),
    (1.43, ue.Vector(472, -355, 119)),
    (1.47, ue.Vector(476, -360, 114)),
    (2.00, ue.Vector(466, -350, 112)),
]
errs = []
for t, loc in moves:
    rot = ue.MathLibrary.find_look_at_rotation(loc, target)
    frame = ue.FrameNumber(int(round(t * FPS)))
    vals = [loc.x, loc.y, loc.z, rot.roll, rot.pitch, rot.yaw]
    for idx, v in enumerate(vals):
        try:
            chans[idx].add_key(frame, float(v), 0.0, ue.MovieSceneTimeUnit.DISPLAY_RATE,
                               ue.MovieSceneKeyInterpolation.AUTO)
        except Exception as e:
            errs.append("ch%d@%.2f: %s" % (idx, t, e))
            break
mark("camera move", key_errors=errs[:4])

# hero animation
anim_track = hero_b.add_track(ue.MovieSceneSkeletalAnimationTrack)
idle = AL.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle")
charged = AL.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_ChargedAttack")
s_atk = anim_track.add_section()
s_atk.set_range_seconds(0.0, 1.8333 - 0.40)
p = ue.MovieSceneSkeletalAnimationParams(animation=charged)
p.set_editor_property("start_frame_offset", ue.FrameNumber(12))
s_atk.set_editor_property("params", p)
mark("animation")

# beam
try:
    n_track = beam_b.add_track(ue.MovieSceneNiagaraSystemTrack)
    n_sec = n_track.add_section()
    n_sec.set_range_seconds(0.40, DUR)
    mark("beam track")
except Exception as e:
    mark("beam track FAILED", beam_err=str(e))

AL.save_asset(FULL)
mark("saved")
