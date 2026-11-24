import json
import unreal as ue

out = {}
AL = ue.EditorAssetLibrary
want = [
    "/Game/EnergyBeamV2/FX/NS_EnergyChargeBeam",
    "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple",
    "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_ChargedAttack",
    "/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle",
]
out["assets"] = {p: bool(AL.does_asset_exist(p)) for p in want}
reg = ue.AssetRegistryHelpers.get_asset_registry()
out["attack_folder"] = sorted(str(a.asset_name) for a in reg.get_assets_by_path("/Game/Characters/Mannequins/Anims/Unarmed/Attack", recursive=True))
out["api"] = {
    "MoviePipelineQueueEngineSubsystem": hasattr(ue, "MoviePipelineQueueEngineSubsystem"),
    "LevelSequenceFactoryNew": hasattr(ue, "LevelSequenceFactoryNew"),
    "MovieSceneSequenceExtensions": hasattr(ue, "MovieSceneSequenceExtensions"),
    "CineCameraActor": hasattr(ue, "CineCameraActor"),
    "MoviePipelineDeferredPassBase": hasattr(ue, "MoviePipelineDeferredPassBase"),
    "MoviePipelinePIEExecutor": hasattr(ue, "MoviePipelinePIEExecutor"),
    "MoviePipelineNewProcessExecutor": hasattr(ue, "MoviePipelineNewProcessExecutor"),
}
with open("/tmp/ue_probe.json", "w") as f:
    json.dump(out, f, indent=1)
