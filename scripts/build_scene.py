import json
import unreal as ue

LEVEL = "/Game/Shot/L_Shot"
STEPS = []

INFO = {}

def mark(name, **kw):
    STEPS.append(name)
    INFO.update(kw)
    with open("/tmp/ue_scene.json", "w") as f:
        json.dump({"steps": STEPS, "info": INFO}, f, indent=1)

mark("start")
levels = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
AL = ue.EditorAssetLibrary

if AL.does_asset_exist(LEVEL):
    levels.load_level(LEVEL)
    for a in actors.get_all_level_actors():
        actors.destroy_actor(a)
    mark("level loaded and cleared")
else:
    if not levels.new_level(LEVEL):
        raise RuntimeError("new_level failed")
    mark("level created")

def load(path):
    a = AL.load_asset(path)
    if not a:
        raise RuntimeError("missing " + path)
    return a

def static(mesh, loc, scale=(1, 1, 1), rot=(0, 0, 0), label=None, material=None):
    a = actors.spawn_actor_from_class(ue.StaticMeshActor, ue.Vector(*loc), ue.Rotator(*rot))
    a.static_mesh_component.set_static_mesh(mesh)
    a.set_actor_scale3d(ue.Vector(*scale))
    if material:
        a.static_mesh_component.set_material(0, material)
    if label:
        a.set_actor_label(label)
    return a

plane = load("/Game/LevelPrototyping/Meshes/SM_Plane")
cube = load("/Game/LevelPrototyping/Meshes/SM_Cube")
reg = ue.AssetRegistryHelpers.get_asset_registry()
grid = None
for a in reg.get_assets_by_path("/Game/LevelPrototyping", recursive=True):
    if str(a.asset_name) == "MI_PrototypeGrid_Gray":
        grid = a.get_asset()
        mark("grid material", grid_path=str(a.package_name))
        break
if grid is None:
    mark("grid material NOT FOUND")
static(plane, (0, 0, 0), scale=(150, 150, 1), label="Floor", material=grid)
mark("floor")

for i, (x, y, sx, sy, sz) in enumerate([
    (1700, -980, 5, 5, 12),
    (2400, 720, 7, 7, 19),
    (1200, 1450, 4, 10, 7),
    (2900, -150, 10, 4, 28),
]):
    static(cube, (x, y, 0), scale=(sx, sy, sz), label="Block_%d" % i, material=grid)
mark("blocks")

hero = actors.spawn_actor_from_class(ue.SkeletalMeshActor, ue.Vector(0, 0, 0), ue.Rotator(0, 0, 0))
hero.set_actor_label("Hero")
smc = hero.skeletal_mesh_component
skm = load("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
try:
    smc.set_skeletal_mesh_asset(skm)
except Exception:
    smc.set_skeletal_mesh(skm)
mark("hero")

beam = actors.spawn_actor_from_class(ue.NiagaraActor, ue.Vector(0, 0, 0), ue.Rotator(0, 0, 0))
beam.set_actor_label("Beam")
nc = beam.get_component_by_class(ue.NiagaraComponent)
nc.set_asset(load("/Game/EnergyBeamV2/FX/NS_EnergyChargeBeam"))
nc.set_auto_activate(False)
# сгусток живёт в руке, иначе удар проходит мимо него
SOCKET = "HandGrip_R" if smc.does_socket_exist("HandGrip_R") else "hand_r"
beam.attach_to_component(smc, SOCKET,
                         ue.AttachmentRule.SNAP_TO_TARGET,
                         ue.AttachmentRule.SNAP_TO_TARGET,
                         ue.AttachmentRule.KEEP_WORLD, False)
# поворот не наследуем от кости: луч всегда бьёт туда, куда смотрит персонаж
nc.set_editor_property("relative_scale3d", ue.Vector(0.35, 0.35, 0.35))
rot_notes = []
try:
    nc.set_editor_property("absolute_rotation", True)
    rot_notes.append("absolute_rotation")
except Exception as e:
    rot_notes.append("abs fail: %s" % e)
for setter in ("set_world_rotation", "k2_set_world_rotation"):
    if hasattr(nc, setter):
        try:
            getattr(nc, setter)(ue.Rotator(0, 0, 0), False, False)
            rot_notes.append(setter)
            break
        except Exception as e:
            rot_notes.append("%s fail: %s" % (setter, e))
mark("beam", socket=SOCKET, rotation=rot_notes, beam_at=[round(v, 1) for v in (nc.get_world_location().x, nc.get_world_location().y, nc.get_world_location().z)])

sky_atm = actors.spawn_actor_from_class(ue.SkyAtmosphere, ue.Vector(), ue.Rotator())
sky_atm.set_actor_label("SkyAtmosphere")

key = actors.spawn_actor_from_class(ue.DirectionalLight, ue.Vector(0, 0, 350), ue.Rotator(pitch=-32, yaw=-118))
key.set_actor_label("KeyLight")
kc = key.get_component_by_class(ue.DirectionalLightComponent)
kc.set_editor_property("intensity", 1.6)
kc.set_editor_property("light_color", ue.Color(237, 225, 206, 255))
kc.set_editor_property("atmosphere_sun_light", True)

fill = actors.spawn_actor_from_class(ue.DirectionalLight, ue.Vector(0, 0, 320), ue.Rotator(pitch=-52, yaw=66))
fill.set_actor_label("FillLight")
fc = fill.get_component_by_class(ue.DirectionalLightComponent)
fc.set_editor_property("intensity", 0.5)
fc.set_editor_property("cast_shadows", False)
fc.set_editor_property("atmosphere_sun_light", False)

amb = actors.spawn_actor_from_class(ue.SkyLight, ue.Vector(0, 0, 600), ue.Rotator())
amb.set_actor_label("SkyLight")
ac = amb.get_component_by_class(ue.SkyLightComponent)
ac.set_editor_property("intensity", 0.45)
ac.set_editor_property("real_time_capture", True)

rim = actors.spawn_actor_from_class(ue.PointLight, ue.Vector(-70, 150, 230), ue.Rotator())
rim.set_actor_label("RimLight")
rl = rim.get_component_by_class(ue.PointLightComponent)
rl.set_editor_property("intensity", 700.0)
rl.set_editor_property("attenuation_radius", 900.0)
rl.set_editor_property("light_color", ue.Color(150, 190, 255, 255))

fog = actors.spawn_actor_from_class(ue.ExponentialHeightFog, ue.Vector(0, 0, -120), ue.Rotator())
fog.set_actor_label("Fog")
mark("lights")

loc = ue.Vector(70, 720, 168)
target = ue.Vector(140, 15, 108)
rot = ue.MathLibrary.find_look_at_rotation(loc, target)
cam = actors.spawn_actor_from_class(ue.CineCameraActor, loc, rot)
cam.set_actor_label("ShotCam")
cc = cam.get_component_by_class(ue.CineCameraComponent)
cc.set_editor_property("current_focal_length", 30.0)
pp = cc.get_editor_property("post_process_settings")
for prop, val in (("bloom_intensity", 0.45), ("auto_exposure_method", ue.AutoExposureMethod.AEM_MANUAL),
                  ("auto_exposure_apply_physical_camera_exposure", False),
                  ("auto_exposure_bias", -1.45), ("motion_blur_amount", 0.0)):
    pp.set_editor_property("override_" + prop, True)
    pp.set_editor_property(prop, val)
cc.set_editor_property("post_process_settings", pp)
ue.get_editor_subsystem(ue.UnrealEditorSubsystem).set_level_viewport_camera_info(loc, rot)
mark("camera")

if not levels.save_current_level():
    raise RuntimeError("save_current_level failed")
mark("saved")
