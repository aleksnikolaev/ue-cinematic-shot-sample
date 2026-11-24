import json
import os
import unreal as ue

RESX = int(os.environ.get("SHOT_RESX", "1920"))
RESY = int(os.environ.get("SHOT_RESY", "1080"))
TEMPORAL = int(os.environ.get("SHOT_TEMPORAL", "4"))

OUT = {"found": {}, "steps": []}
def mark(s, **kw):
    OUT["steps"].append(s); OUT.update(kw)
    with open("/tmp/ue_mrq.json", "w") as f:
        json.dump(OUT, f, indent=1)

names = ["MoviePipelinePrimaryConfig", "MoviePipelineDeferredPassBase", "MoviePipelineImageSequenceOutput_PNG",
         "MoviePipelineImageSequenceOutput_JPG", "MoviePipelineOutputSetting", "MoviePipelineAntiAliasingSetting",
         "MoviePipelineGameOverrideSetting", "MoviePipelineMasterConfig", "MoviePipelineConsoleVariableSetting"]
OUT["found"] = {n: hasattr(ue, n) for n in names}
mark("probed")

AL = ue.EditorAssetLibrary
TOOLS = ue.AssetToolsHelpers.get_asset_tools()
PATH, NAME = "/Game/Shot", "MRQ_Config"
FULL = PATH + "/" + NAME
if AL.does_asset_exist(FULL):
    AL.delete_asset(FULL)

cfg_cls = ue.MoviePipelinePrimaryConfig if hasattr(ue, "MoviePipelinePrimaryConfig") else ue.MoviePipelineMasterConfig
factory = None
for fname in ["MoviePipelinePrimaryConfigFactory", "MoviePipelineMasterConfigFactory"]:
    if hasattr(ue, fname):
        factory = getattr(ue, fname)()
        break
cfg = TOOLS.create_asset(NAME, PATH, cfg_cls, factory)
mark("config asset created", factory=str(factory))

cfg.find_or_add_setting_by_class(ue.MoviePipelineDeferredPassBase)
mark("deferred pass")

png = cfg.find_or_add_setting_by_class(ue.MoviePipelineImageSequenceOutput_PNG)
mark("png output")

osetting = cfg.find_or_add_setting_by_class(ue.MoviePipelineOutputSetting)
OUTDIR = os.environ.get("SHOT_OUT", "{project_dir}/../render")
osetting.set_editor_property("output_directory", ue.DirectoryPath(OUTDIR))
osetting.set_editor_property("file_name_format", "shot.{frame_number}")
osetting.set_editor_property("output_resolution", ue.IntPoint(RESX, RESY))
osetting.set_editor_property("use_custom_frame_rate", True)
osetting.set_editor_property("output_frame_rate", ue.FrameRate(30, 1))
osetting.set_editor_property("override_existing_output", True)
mark("output setting")

try:
    aa = cfg.find_or_add_setting_by_class(ue.MoviePipelineAntiAliasingSetting)
    aa.set_editor_property("spatial_sample_count", 1)
    aa.set_editor_property("temporal_sample_count", TEMPORAL)
    aa.set_editor_property("override_anti_aliasing", True)
    aa.set_editor_property("anti_aliasing_method", ue.AntiAliasingMethod.AAM_TSR)
    mark("anti aliasing")
except Exception as e:
    mark("anti aliasing FAILED", aa_err=str(e))

try:
    go = cfg.find_or_add_setting_by_class(ue.MoviePipelineGameOverrideSetting)
    go.set_editor_property("game_mode_override", None)
    mark("game override")
except Exception as e:
    mark("game override skipped", go_err=str(e))

# выключить размазывание движением, кадр должен быть резким
try:
    cv = cfg.find_or_add_setting_by_class(ue.MoviePipelineConsoleVariableSetting)
    done = False
    try:
        entries = []
        for name, val in [("r.MotionBlurQuality", 0.0), ("r.DefaultFeature.MotionBlur", 0.0)]:
            e = ue.MoviePipelineConsoleVariableEntry()
            e.set_editor_property("name", name)
            e.set_editor_property("value", val)
            e.set_editor_property("is_enabled", True)
            entries.append(e)
        cv.set_editor_property("console_variables", entries)
        done = True
    except Exception as e1:
        try:
            cv.set_editor_property("console_variables", {"r.MotionBlurQuality": 0.0, "r.DefaultFeature.MotionBlur": 0.0})
            done = True
        except Exception as e2:
            mark("cvar FAILED", cvar_err="%s | %s" % (e1, e2))
    if done:
        mark("console variables")
except Exception as e:
    mark("cvar setting FAILED", cvar_outer=str(e))

AL.save_asset(FULL)
mark("saved", res=[RESX, RESY], temporal=TEMPORAL)
