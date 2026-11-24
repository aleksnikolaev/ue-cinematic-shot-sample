import json
import unreal as ue

out = {}
names = ["MovieSceneCameraCutTrack", "MovieScene3DTransformTrack", "MovieSceneSkeletalAnimationTrack",
         "MovieSceneNiagaraSystemTrack", "MovieSceneSkeletalAnimationParams", "MovieSceneObjectBindingID",
         "LevelSequence", "SequencerTools", "MovieSceneScriptingDoubleChannel", "MovieSceneBindingExtensions",
         "MovieSceneSectionExtensions", "MovieSceneTrackExtensions", "MovieSceneNiagaraSystemSpawnSection"]
out["classes"] = {n: hasattr(ue, n) for n in names}
out["LevelSequence_methods"] = sorted(m for m in dir(ue.LevelSequence) if any(
    k in m for k in ("add_", "playback", "display_rate", "binding", "tick_resolution")))
out["Section_methods"] = sorted(m for m in dir(ue.MovieSceneSection) if any(
    k in m for k in ("range", "channel", "start", "end")))
out["Track_methods"] = sorted(m for m in dir(ue.MovieSceneTrack) if "section" in m)
if hasattr(ue, "MovieSceneSkeletalAnimationParams"):
    out["AnimParams_props"] = sorted(p for p in dir(ue.MovieSceneSkeletalAnimationParams) if not p.startswith("_"))[:30]
with open("/tmp/ue_probe3.json", "w") as f:
    json.dump(out, f, indent=1)
