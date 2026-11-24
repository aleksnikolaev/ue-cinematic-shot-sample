import json
import unreal as ue

OUT = {"steps": []}
def mark(s, **kw):
    OUT["steps"].append(s); OUT.update(kw)
    with open("/tmp/ue_toon.json", "w") as f:
        json.dump(OUT, f, indent=1)

AL = ue.EditorAssetLibrary
TOOLS = ue.AssetToolsHelpers.get_asset_tools()
MAT = ue.MaterialEditingLibrary
FOLDER, NAME = "/Game/Shot", "M_Toon"
FULL = FOLDER + "/" + NAME
OFF = 0.0009   # смещение пробы в экранных UV, примерно пиксель на 1080p

if AL.does_asset_exist(FULL):
    AL.delete_asset(FULL)
mat = TOOLS.create_asset(NAME, FOLDER, ue.Material, ue.MaterialFactoryNew())
mat.set_editor_property("material_domain", ue.MaterialDomain.MD_POST_PROCESS)
mark("material created")

sp = MAT.create_material_expression(mat, ue.MaterialExpressionScreenPosition, -1500, 0)

def shifted(dx, dy, y):
    """UV со смещением: ScreenPosition + константа"""
    if dx == 0 and dy == 0:
        return sp
    c = MAT.create_material_expression(mat, ue.MaterialExpressionConstant2Vector, -1400, y)
    c.set_editor_property("r", dx)
    c.set_editor_property("g", dy)
    add = MAT.create_material_expression(mat, ue.MaterialExpressionAdd, -1250, y)
    assert MAT.connect_material_expressions(sp, "ViewportUV", add, "A")
    assert MAT.connect_material_expressions(c, "", add, "B")
    return add

def tap(tex_id, dx, dy, y):
    node = MAT.create_material_expression(mat, ue.MaterialExpressionSceneTexture, -1050, y)
    node.set_editor_property("scene_texture_id", tex_id)
    src = shifted(dx, dy, y)
    pin = "ViewportUV" if src is sp else ""
    assert MAT.connect_material_expressions(src, pin, node, "UVs"), "UV не подключился"
    return node

DEPTH = ue.SceneTextureId.PPI_SCENE_DEPTH
NORMAL = ue.SceneTextureId.PPI_WORLD_NORMAL
COLOR = ue.SceneTextureId.PPI_POST_PROCESS_INPUT0

taps = [
    ("c",  COLOR,  0, 0, -400),
    ("d0", DEPTH,  0, 0, -250),
    ("dr", DEPTH,  OFF, 0, -100),
    ("dd", DEPTH,  0, OFF, 50),
    ("n0", NORMAL, 0, 0, 200),
    ("nr", NORMAL, OFF, 0, 350),
    ("nd", NORMAL, 0, OFF, 500),
]
nodes = {name: tap(tid, dx, dy, y) for name, tid, dx, dy, y in taps}
mark("taps built")

HLSL = """
float3 base = c;

float depthEdge = abs(dr.r - d0.r) + abs(dd.r - d0.r);
depthEdge = saturate(depthEdge / max(d0.r * 0.03, 1.0));

float normalEdge = (1.0 - dot(n0, nr)) + (1.0 - dot(n0, nd));
normalEdge = saturate(normalEdge * 7.0);

float edge = saturate(max(depthEdge, normalEdge * 0.85));

float lum = dot(base, float3(0.299, 0.587, 0.114));
float steps = 5.0;
// гамма-подъём до разбивки, иначе тени схлопываются в чёрный
float lifted = pow(saturate(lum), 0.6);
float banded = pow(floor(lifted * steps + 0.4) / steps, 1.0 / 0.6);
float3 toned = base * (banded / max(lum, 0.0001));
float keep = smoothstep(0.8, 1.3, lum);
float3 col = lerp(toned, base, keep);

return col * (1.0 - edge * 0.8);
"""

custom = MAT.create_material_expression(mat, ue.MaterialExpressionCustom, -600, 0)
pins = []
for name in ["c", "d0", "dr", "dd", "n0", "nr", "nd"]:
    p = ue.CustomInput()
    p.set_editor_property("input_name", name)
    pins.append(p)
custom.set_editor_property("inputs", pins)
custom.set_editor_property("code", HLSL)
custom.set_editor_property("output_type", ue.CustomMaterialOutputType.CMOT_FLOAT3)
custom.set_editor_property("description", "Toon")
for name in ["c", "d0", "dr", "dd", "n0", "nr", "nd"]:
    assert MAT.connect_material_expressions(nodes[name], "Color", custom, name), "не подключён " + name
MAT.connect_material_property(custom, "", ue.MaterialProperty.MP_EMISSIVE_COLOR)
MAT.recompile_material(mat)
AL.save_asset(FULL)
mark("material compiled")

levels = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
levels.load_level("/Game/Shot/L_Shot")
cam = {a.get_actor_label(): a for a in actors.get_all_level_actors()}["ShotCam"]
cc = cam.get_component_by_class(ue.CineCameraComponent)
pp = cc.get_editor_property("post_process_settings")
wb = ue.WeightedBlendable(1.0, mat)
pp.set_editor_property("weighted_blendables", ue.WeightedBlendables([wb]))
cc.set_editor_property("post_process_settings", pp)
levels.save_current_level()
mark("attached")
