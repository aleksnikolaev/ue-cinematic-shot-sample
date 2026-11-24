import json
import unreal as ue

SEQ_PATH, SEQ_NAME = "/Game/Shot", "LS_Look"
FULL = SEQ_PATH + "/" + SEQ_NAME
FPS = 30
HOLD = 6          # кадров на один ракурс
START_T = 1.30    # момент разряда
STEPS = []
INFO = {}
def mark(s, **kw):
    STEPS.append(s); INFO.update(kw)
    with open("/tmp/ue_look2.json", "w") as f:
        json.dump({"steps": STEPS, "info": INFO}, f, indent=1)

CANDIDATES = [
    ("a_side",        (150, -620, 140),  (350, 20, 110),  35.0),
    ("b_front_three", (520, -420, 130),  (40, 20, 115),   40.0),
    ("c_shoulder",    (-330, -230, 190), (420, 60, 110),  35.0),
    ("d_low_side",    (200, -430, 60),   (330, 10, 130),  45.0),
    ("e_high_side",   (120, -520, 300),  (300, 30, 90),   35.0),
    ("f_wide_side",   (300, -860, 180),  (320, 0, 110),   28.0),
]
DUR = START_T + len(CANDIDATES) * HOLD / float(FPS)

levels = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
AL = ue.EditorAssetLibrary
TOOLS = ue.AssetToolsHelpers.get_asset_tools()
levels.load_level("/Game/Shot/L_Shot")
by_label = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
mark("level", labels=sorted(by_label))

if AL.does_asset_exist(FULL):
    AL.delete_asset(FULL)
seq = TOOLS.create_asset(SEQ_NAME, SEQ_PATH, ue.LevelSequence, ue.LevelSequenceFactoryNew())
seq.set_display_rate(ue.FrameRate(FPS, 1))
seq.set_playback_start_seconds(0.0)
seq.set_playback_end_seconds(DUR)

cam_b = seq.add_possessable(by_label["ShotCam"])
hero_b = seq.add_possessable(by_label["Hero"])
beam_b = seq.add_possessable(by_label["Beam"])
mark("bindings")

cut_track = seq.add_track(ue.MovieSceneCameraCutTrack)
cut = cut_track.add_section()
cut.set_range_seconds(0.0, DUR)
cut.set_camera_binding_id(seq.get_binding_id(cam_b))

tr = cam_b.add_track(ue.MovieScene3DTransformTrack).add_section()
tr.set_range_seconds(0.0, DUR)
ch = tr.get_all_channels()
errs = []
for i, (name, loc, look, fov) in enumerate(CANDIDATES):
    t = START_T + i * HOLD / float(FPS)
    v = ue.Vector(*loc)
    rot = ue.MathLibrary.find_look_at_rotation(v, ue.Vector(*look))
    frame = ue.FrameNumber(int(round(t * FPS)))
    for idx, val in enumerate([v.x, v.y, v.z, rot.roll, rot.pitch, rot.yaw]):
        try:
            ch[idx].add_key(frame, float(val), 0.0, ue.MovieSceneTimeUnit.DISPLAY_RATE,
                            ue.MovieSceneKeyInterpolation.CONSTANT)
        except Exception as e:
            errs.append(str(e)); break
    # первый ракурс держим и с нулевого кадра
    if i == 0:
        for idx, val in enumerate([v.x, v.y, v.z, rot.roll, rot.pitch, rot.yaw]):
            try:
                ch[idx].add_key(ue.FrameNumber(0), float(val), 0.0, ue.MovieSceneTimeUnit.DISPLAY_RATE,
                                ue.MovieSceneKeyInterpolation.CONSTANT)
            except Exception as e:
                errs.append(str(e)); break
mark("camera jumps", key_errors=errs[:3], duration=DUR)

anim_track = hero_b.add_track(ue.MovieSceneSkeletalAnimationTrack)
charged = AL.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_ChargedAttack")
s_atk = anim_track.add_section()
s_atk.set_range_seconds(0.0, 1.8333 - 0.40)
p = ue.MovieSceneSkeletalAnimationParams(animation=charged)
p.set_editor_property("start_frame_offset", ue.FrameNumber(12))
s_atk.set_editor_property("params", p)
mark("animation")

n_sec = beam_b.add_track(ue.MovieSceneNiagaraSystemTrack).add_section()
n_sec.set_range_seconds(0.40, DUR)
mark("beam")

AL.save_asset(FULL)
mark("saved")
