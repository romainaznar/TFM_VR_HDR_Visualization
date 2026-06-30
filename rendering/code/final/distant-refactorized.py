import math

import drjit as dr
import mitsuba as mi

import datetime
import numpy as np

# print(mi.__file__)
mi.set_log_level(mi.LogLevel.Info)

# mi.set_variant('llvm_ad_spectral')
mi.set_variant('cuda_ad_spectral')

# from MyNormalMap import MyNormalMap
# mi.register_bsdf("mynormalmap", lambda props: MyNormalMap(props))

from mitsuba import ScalarTransform4f as T
import pandas as pd

from sunsky_configurations import SUNSKY_CONFIGURATIONS

def create_emitter_spdfile(position, spd_filename):
    return {
            'type': 'point',
            'position': position,
            'intensity': {
                'type': 'spectrum',
                'filename': spd_filename
            }
        }


def create_sphere_light_file(center, radius, file):
    return {
        'type': 'sphere',
        'center': center,
        'radius': radius,
        'emitter': {
            'type': 'area',
            'radiance': {
                'type': 'spectrum',
                'filename': file
            }
        }
    }

def create_obj_file_light_file(obj_file, radiance_file):
    return {
        'type': 'obj',
        'filename': obj_file,
        'emitter': {
            'type': 'area',
            'radiance': {
                'type': 'spectrum',
                'filename': radiance_file
            }
        },
        'bsdf': {
            'type': 'normalmap',
            'normalmap': {
                'type': 'bitmap',
                'raw': True,
                'filename': 'textures/normalmap.png'
            },
            'bsdf': {
                'type': 'diffuse',
                'reflectance': {
                'type': 'rgb',
                'value': [1,1,1],
                }
            }
        }
    }

def create_distant_directional_emitter(dirBlender, file):
    dirMitsuba = [dirBlender[0], dirBlender[2], -dirBlender[1]]
    return {
        'type' : 'directional',
        'direction': dirMitsuba,
        'irradiance':{
            'type':'spectrum',
            'filename': file,
        }
    }

def create_constant_enviroment_emitter(file):
    return{
        'type': 'constant',
        'radiance': {
            'type': 'spectrum',
            'filename': file,
        }
    }

def create_spd_file_and_emitter(sheet_name, number, filepath='data/IT1073.xlsx'):
    # Adjust to use the actual column names for wavelength and intensity
    df = pd.read_excel(filepath, sheet_name=sheet_name, skiprows=1)
    df = df.drop([0, 1])
    df = df.drop(df.columns[0], axis=1)
    df = df.rename(columns={'ID medida': 'Longitud de onda'})
    output_filename = f"spdvid/{sheet_name}_{number}.spd"

    with open(output_filename, 'w') as file:
        for index, row in df.iterrows():
            # Ensure the correct intensity column is referenced in the f-string
            #file.write(f"{row['Longitud de onda']} {row[number]*1000}\n")
            file.write(f"{row['Longitud de onda']} {row[number]}\n")

    return create_emitter_spdfile([6.5284 , 1.1359 , -16.852 ], output_filename)
    #return create_sphere_light_file([6.5284 , 1.1359 , -16.852 ],  0.05, output_filename)


def create_obj_shape(filename, normal_texture, color_texture):
    return {
        'type': 'obj',
        'filename': filename,
        'face_normals': False,
        #'bsdf': {
        #    'type': 'twosided',
            'bsdf': {
                'type': 'normalmap',#mynormalmap
                'normalmap': {
                    'type': 'bitmap',
                    'raw': True,
                    'filename': normal_texture
                },
                'bsdf': {
                    'type': 'diffuse',
                    'reflectance': {
                        'type': 'bitmap',
                        'filename': color_texture,
                    },    
                },
            },
        #}
    }

def create_shape_rgb(filename, color):
    return {
        'type': 'obj',
        'filename': filename,
        'bsdf': {
            'type': 'normalmap',
            'normalmap': {
                'type': 'bitmap',
                'raw': True,
                'filename': 'textures/normalmap.png'
            },
            'bsdf': {
                'type': 'diffuse',
                'reflectance': {
                'type': 'rgb',
                'value': color,
                }
            }
        }
    }


def create_shape_dielectric(filename):
    return {
        'type': 'obj',
        'filename': filename,
        'bsdf': {
            'type': 'normalmap',
            'normalmap': {
                'type': 'bitmap',
                'raw': True,
                'filename': 'textures/normalmap.png'
            },
            'bsdf': {
                'type': 'dielectric',
                'int_ior': 'bk7',
                'ext_ior':'air', 
            }
        }
    }


# camera when we use cuda
from mitsuba import ScalarTransform4f as T, ScalarPoint3f, Vector3f


def ConvertCSVtoSPD_lig(csv_file_path, spd_filename):
    # Read the CSV file, skipping the first 13 rows
    df = pd.read_csv(csv_file_path, delimiter=',', skiprows=13)
   
    # Write the spectral data to an SPD file
    with open(spd_filename, 'w') as file:
        for index, row in df.iterrows():
            file.write(f"{row['wavelength']} {row[' intensity']}\n")
    #print(f"SPD file '{spd_filename}' has been created.")

# artificial
def create_spd_file(sheet_name, position, filepath= 'data/IT1072.xlsx'):
    flame_area = 0.0013378719
    intensity_column = f'Unnamed: {position}'

    df = pd.read_excel(filepath, sheet_name=sheet_name, usecols=['Longitud de onda (nm)', intensity_column])
    
    df = df.drop(df.index[0])
    output_filename = f"spdFiles/XII/{sheet_name}_position{position}_by_flamearea.spd"

    with open(output_filename, 'w') as file:
        for index, row in df.iterrows():
            # Ensure the correct intensity column is referenced in the f-string
            #file.write(f"{row['Longitud de onda (nm)']} {(row[intensity_column]*1000)/flame_area}\n")
            file.write(f"{row['Longitud de onda (nm)']} {(row[intensity_column])/flame_area}\n")


def add_SXII_shapes(shapes, use_gray_albedo = False):
    t1 = 'textures/pedret_XII/Pedret_X_color_1.png'
    t2 = 'textures/pedret_XII/Pedret_X_color_2.png'
    t3 = 'textures/pedret_XII/Pedret_XII_color_absC.png'
    t4 = 'textures/pedret_XII/Pedret_XII_color_absN.png'
    t5 = 'textures/pedret_XII/Pedret_XII_color_absS.png'
    t6 = 'textures/pedret_XII/Pedret_XII_color_nau.png'
    if use_gray_albedo:
        t1 = t2 = t3 = t4 = t5 = t6 = 'textures/midgray.png'

    shapes.append(create_obj_shape('model/XII_2/Pedret_XII.baked-1.obj', 'textures/pedret_XII/Pedret_X_normals_1.png', t1))
    shapes.append(create_obj_shape('model/XII_2/Pedret_XII.baked-2.obj', 'textures/pedret_XII/Pedret_X_normals_2.png', t2))
    shapes.append(create_obj_shape('model/XII_2/Pedret_XII.baked-absC.obj', 'textures/pedret_XII/Pedret_XII_normals_absC.png', t3))
    shapes.append(create_obj_shape('model/XII_2/Pedret_XII.baked-absN.obj', 'textures/pedret_XII/Pedret_XII_normals_absN.png', t4))
    shapes.append(create_obj_shape('model/XII_2/Pedret_XII.baked-absS.obj', 'textures/pedret_XII/Pedret_XII_normals_absS.png', t5))
    shapes.append(create_obj_shape('model/XII_2/Pedret_XII.baked-nau.obj', 'textures/pedret_XII/Pedret_XII_normals_nau.png', t6))

def add_SXIII_shapes(shapes, use_gray_albedo = False):
    t1 = 'textures/pedret_XII/Pedret_XIII_color_1.png'
    t2 = 'textures/pedret_XII/Pedret_XIII_color_2.png'
    t3 = 'textures/pedret_XII/Pedret_XII_color_absC.png'
    t4 = 'textures/pedret_XII/Pedret_XII_color_absN.png'
    t5 = 'textures/pedret_XII/Pedret_XII_color_absS.png'
    t6 = 'textures/pedret_XII/Pedret_XII_color_nau.png'
    if use_gray_albedo:
        t1 = t2 = t3 = t4 = t5 = t6 = 'textures/midgray.png'

    shapes.append(create_obj_shape('model/XIII/Pedret_XIII_1.obj', 'textures/pedret_XII/Pedret_XIII_normals_1.png', t1))
    shapes.append(create_obj_shape('model/XIII/Pedret_XIII_2.obj', 'textures/pedret_XII/Pedret_XIII_normals_2.png', t2))
    shapes.append(create_obj_shape('model/XIII/Pedret_XIII_absC.obj', 'textures/pedret_XII/Pedret_XII_normals_absC.png', t3))
    shapes.append(create_obj_shape('model/XIII/Pedret_XIII_absN.obj', 'textures/pedret_XII/Pedret_XII_normals_absN.png', t4))
    shapes.append(create_obj_shape('model/XIII/Pedret_XIII_absS.obj', 'textures/pedret_XII/Pedret_XII_normals_absS.png', t5))
    shapes.append(create_obj_shape('model/XIII/Pedret_XIII_nau.obj', 'textures/pedret_XII/Pedret_XII_normals_nau.png', t6))

def add_corona_shapes(shapes):
    color = [0.05, 0.05, 0.05]
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Anella.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Anella2.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Base.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Cadena.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Cadena2.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Cadena3.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Ganxo.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Ganxo2.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Ganxo3.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Ganxo4.obj', color))
    shapes.append(create_shape_dielectric('iluminació/c1/Corona/Llums.obj'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Corona/flama1.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Corona/flama2.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Corona/flama3.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Corona/flama4.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Corona/flama5.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Corona/flama6.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))

def add_llantia_shapes(shapes):
    #llantia1
    shapes.append(create_shape_rgb('iluminació/c1/Llantia1/Argolla.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia1/Cordill1Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia1/Cordill2Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia1/Cordill3Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia1/Cordill4Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_dielectric('iluminació/c1/Llantia1/Llum.obj'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Llantia1/Flama.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))

    #llantia2
    shapes.append(create_shape_rgb('iluminació/c1/Llantia2/Argolla.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia2/Cordill1Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia2/Cordill2Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia2/Cordill3Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia2/Cordill4Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_dielectric('iluminació/c1/Llantia2/Llum.obj'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Llantia2/Flama.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))

def add_candelers(shapes):
    #candeler 1
    shapes.append(create_shape_rgb('iluminació/c2/candeler1/holder_1.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c2/candeler1/candle_1.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c2/candeler1/candle_wick_1.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c2/candeler1/flame_1.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))

    #candeler 2
    shapes.append(create_shape_rgb('iluminació/c2/candeler2/holder_2.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c2/candeler2/candle_2.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c2/candeler2/candle_wick_2.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c2/candeler2/flame_2.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))

def add_candelers2(shapes):
    #canelobre 1
    shapes.append(create_shape_rgb('iluminació/c3/canelobre1/holder.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre1/candle_2.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre1/candle_wick_2.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c3/canelobre1/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))

    #canelobre 2
    shapes.append(create_shape_rgb('iluminació/c3/canelobre2/holder.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre2/candle_2.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre2/candle_wick_2.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c3/canelobre2/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))


def add_candelers4(shapes):
    #canelobre 1
    shapes.append(create_shape_rgb('iluminació/c3/canelobre1/holder.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre1/candle_2.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre1/candle_wick_2.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c3/canelobre1/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))

    #canelobre 2
    shapes.append(create_shape_rgb('iluminació/c3/canelobre2/holder.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre2/candle_2.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre2/candle_wick_2.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c3/canelobre2/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))

    #canelobre 3
    shapes.append(create_shape_rgb('iluminació/c4/canelobre3/holder_3.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c4/canelobre3/candle_3.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c4/canelobre3/candle_wick_3.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c4/canelobre3/flame_3.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))

    #canelobre 4
    shapes.append(create_shape_rgb('iluminació/c4/canelobre4/holder_4.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c4/canelobre4/candle_4.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c4/canelobre4/candle_wick_4.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c4/canelobre4/flame_4.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))


def add_altar(shapes):
    shapes.append(create_obj_shape('iluminació/Base.obj', "textures/altar/plastersubstance001_Plaster_normal.png", "textures/altar/plastersubstance001_Plaster_basecolor.png"))
    shapes.append(create_obj_shape('iluminació/Llosa.obj', "textures/altar/granite_001_Granite_001_normal.png", "textures/altar/granite_001_Granite_001_basecolor.png"))


def create_scene_from_shapes(building_shapes, lighting_shapes):
    scene_definition = { 'type': 'scene' }
    for i, shape in enumerate(building_shapes):
        scene_definition[f'b_shape{i+1}'] = shape
    for i, shape in enumerate(lighting_shapes):
        scene_definition[f'l_shape{i+1}'] = shape
    return scene_definition

def create_aov_integrator(max_depth):
    return mi.load_dict({
    'type': 'aov',
    'aovs': 'albedo:albedo,normals:sh_normal',#tex_normal
    'integrator': {
        'type': 'path',
        'max_depth': max_depth
    }
    })

FACE_DIRS = {
    "front": np.array([0, 0, -1]),
    "back": np.array([0, 0, 1]),
    "left": np.array([-1, 0, 0]),
    "right": np.array([1, 0, 0]),
    "bottom": np.array([0, -1, 0]),
    "top": np.array([0, 1, 0]),
}

base_center = mi.ScalarPoint3f(0.690537, 5.13331, -1.29192)

def get_stereo_face(face_dir, eye=None, ipd=0.064):
    origin, target, up = face_to_lookat(
        base_center,
        face_dir
    )

    origin = np.array([origin.x, origin.y, origin.z])
    target = np.array([target.x, target.y, target.z])
    up = np.array([up.x, up.y, up.z])

    forward = target - origin
    forward /= np.linalg.norm(forward)

    right = np.cross(up, forward)
    right /= np.linalg.norm(right)

    if eye == "left":
        offset = -right * (ipd / 2.0)
    elif eye == "right":
        offset = right * (ipd / 2.0)
    else:
        offset = np.zeros(3)

    origin += offset
    target += offset

    return (
        mi.ScalarPoint3f(*origin),
        mi.ScalarPoint3f(*target),
        mi.ScalarVector3f(*up)
    )

def add_camera(scene, translation, target, up, fov=90, upscale=1):
    orig_width = int(1024 * upscale)
    orig_height = int(1024 * upscale)
    
    padding = 16
    new_width = orig_width + 2 * padding
    new_height = orig_height + 2 * padding
    
    fov_rad = math.radians(fov)
    adjusted_fov_rad = 2 * math.atan(math.tan(fov_rad / 2.0) * (new_width / orig_width))
    adjusted_fov = math.degrees(adjusted_fov_rad)

    to_world = T().look_at(
        origin=translation,
        target=target,
        up=up
    )

    scene['sensor'] = {
        'type': 'perspective',
        'fov_axis': 'x',
        'fov': adjusted_fov,
        'near_clip': 0.1,
        'far_clip': 1000.0,
        'to_world': to_world,
        'sampler': {
            'type': 'independent',
            'sample_count': 4
        },
        'film': {
            'type': 'hdrfilm',
            'width': new_width,  
            'height': new_height,  
            'filter': {'type': 'box'}
        }
    }

def face_to_lookat(center, face):
    forward = FACE_DIRS[face]

    if face == "top":
        up = np.array([0, 0, 1])
    elif face == "bottom":
        up = np.array([0, 0, -1])
    else:
        up = np.array([0, 1, 0])

    theta = math.radians(246.0)
    c, s = math.cos(theta), math.sin(theta)
    rot_y = np.array([
        [c, 0, s],
        [0, 1, 0],
        [-s, 0, c]
    ])

    forward = rot_y @ forward
    up = rot_y @ up

    origin = np.array([center.x, center.y, center.z])
    target = origin + forward

    return (
        mi.ScalarPoint3f(*origin),
        mi.ScalarPoint3f(*target),
        mi.ScalarVector3f(*up)
    )

def pv7():
    translation = mi.Point3f(-3.04298, 5.0747, 3.6798)
    rotX  = 99.3053
    rotY  = -0.000209
    rotZ  = -131.466
    fov = 61.9
    return (translation, rotX, rotY, rotZ, fov)


def my_render(
    scene,
    spp,
    integrator,
    exposure,
    basename,
    save_albedo=False,
    save_normals=False,
    save_noisy=True,
    exposure_noisy=1,
):
    sensor = scene.sensors()[0]
    to_sensor = sensor.world_transform().inverse()
    print("Rendering the scene")
    print(datetime.datetime.now())
    image = mi.render(scene, spp=spp, integrator=integrator)
    print(datetime.datetime.now())

    # save multichannel image
    noisy_multichannel = sensor.film().bitmap()
    # mi.util.write_bitmap("renderPedret/"+basename+"-multichannel.exr", noisy_multichannel)
    # Extract and convert the transform to a numpy array:
    to_sensor_matrix = np.array(
        dr.detach(to_sensor.matrix), dtype=np.float32, order="C"
    )
    # np.save("renderPedret/"+basename+"-to_sensor.npy", to_sensor_matrix)

    # Denoise the rendered image
    mi.set_variant("cuda_ad_spectral")
    to_sensor = mi.cuda_ad_rgb.Transform4f(to_sensor_matrix)
    #    to_sensor = mi.cuda_ad_rgb.Transform4f(to_sensor)
    denoiser = mi.OptixDenoiser(
        input_size=noisy_multichannel.size(), albedo=True, normals=False, temporal=False
    )  # TODO!!!
    denoised = denoiser(
        noisy_multichannel,
        albedo_ch="albedo",
        normals_ch="normals",
        to_sensor=to_sensor,
    )

    # remove overscan
    overscan = 16
    denoised_np = np.array(denoised)
    denoised_cropped = denoised_np[overscan:-overscan, overscan:-overscan, :]
    # denoised_to_save = mi.Bitmap(denoised_cropped, pixel_format=denoised.pixel_format())

    # save denoised image
    # mi.util.write_bitmap("renderPedret/" + basename + "-denoised.exr", denoised_to_save)

    if save_albedo:  # save also albedo and normal map
        # print(noisy_multichannel)
        # print(noisy_multichannel.split())
        mi.util.write_bitmap(
            "renderPedret/" + basename + "-albedo.exr", noisy_multichannel.split()[1][1]
        )
        mi.util.write_bitmap(
            "renderPedret/" + basename + "-albedo.jpg", noisy_multichannel.split()[1][1]
        )

    if save_normals:
        mi.util.write_bitmap(
            "renderPedret/" + basename + "-normal.exr", noisy_multichannel.split()[3][1]
        )
        mi.util.write_bitmap(
            "renderPedret/" + basename + "-normal.jpg", noisy_multichannel.split()[3][1]
        )

    if False:
        denoiser = mi.OptixDenoiser(
            input_size=noisy_multichannel.size(),
            albedo=False,
            normals=False,
            temporal=False,
        )
        denoised2 = denoiser(noisy_multichannel)
        mi.util.write_bitmap("renderPedret/carlos2-denoised-no-albedo.exr", denoised2)
        denoised2 = None

    if exposure != 1:
        print("Adjusting exposure...")
        adjusted_denoised = denoised_cropped * pow(2, exposure)
        mi.util.write_bitmap(
            "renderPedret/" + basename + ".exr", adjusted_denoised
        )

    if save_noisy:
        noisy = dict(noisy_multichannel.split())["<root>"]
        if exposure_noisy != 1:
            print("Adjusting exposure...")
            noisy = np.array(noisy)
            noisy *= pow(2, exposure_noisy)
            mi.util.write_bitmap("renderPedret/" + basename + "-noisy.exr", noisy)

    # mi.set_variant("llvm_ad_spectral")
    mi.set_variant("cuda_ad_spectral")

def generate_shapes(load_church_model, use_gray_albedo):
    shapes = []
    load_church_model(shapes, use_gray_albedo)
    add_altar(shapes)

    return shapes

def generate_C1_shapes():
    shapes = []
    add_corona_shapes(shapes)
    add_llantia_shapes(shapes)
    return shapes

def generate_C2_shapes():
    shapes = []
    add_candelers(shapes)
    return shapes

def generate_C3_shapes():
    shapes = []
    add_candelers2(shapes)
    return shapes

def generate_C4_shapes():
    shapes = []
    add_candelers4(shapes)
    return shapes

def generate_C5_shapes():
    shapes = []
    add_corona_shapes(shapes)
    add_llantia_shapes(shapes)
    add_candelers(shapes)
    add_candelers4(shapes)
    return shapes

def generate_natural_light(moment):
    direction = SUNSKY_CONFIGURATIONS.get(moment).get("sundir")
    sun_file = SUNSKY_CONFIGURATIONS.get(moment).get("sun_file")
    sky_file = SUNSKY_CONFIGURATIONS.get(moment).get("sky_file")
    directional_sun = create_distant_directional_emitter(direction, 'emitters/spd/'+sun_file)#file_sun
    cons_diffuse = create_constant_enviroment_emitter('emitters/spd/'+sky_file)#file_difuse_pedret
    return [directional_sun, cons_diffuse]

def make_filename_compatible(s):
    invalid = r"""#%&{}\<>*?/$!'"@+`|=:, """
    for c in invalid: 
        s = s.replace(c, "")
    return s

def render(basename, upscale, model, artificial_lighting_shape_generator, natural_lighting_generator, sampler, max_depth, exposure, spp, point_of_view, save_noisy, save_albedo = False, save_normals = True, use_gray_albedo = False):
    local_vars = locals()
    del local_vars['artificial_lighting_shape_generator']
    del local_vars['point_of_view']
    del local_vars['basename']
    del local_vars['natural_lighting_generator']
    del local_vars['model']
    # local_vars = make_filename_compatible(str(local_vars))
    # print(local_vars)
    building_shapes = generate_shapes(model, use_gray_albedo)
    lighting_shapes = []
    if artificial_lighting_shape_generator:
        lighting_shapes = artificial_lighting_shape_generator()
    scene_definition = create_scene_from_shapes(building_shapes, lighting_shapes)
    
    if natural_lighting_generator:
        emitters = generate_natural_light(natural_lighting_generator)
        for i, emitter in enumerate(emitters):
            scene_definition[f'emitter{i+1}'] = emitter

    (translation, target, up) = point_of_view
    add_camera(scene_definition, translation=translation, target=target, up=up, fov=90, upscale=upscale)
    print(scene_definition)
    scene = mi.load_dict(scene_definition)
    integrator = create_aov_integrator(max_depth)
    my_render(scene=scene, spp=spp, integrator=integrator, exposure=exposure, basename=basename,
              save_noisy=save_noisy, exposure_noisy=exposure, save_albedo=save_albedo, save_normals=save_normals)


sampler = 'independent'
exposure = 13

spp = 2048

# Left eye
moment = "D3T3"
render(f"LEFT-{moment}-natural-pv_front", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("front", eye="left"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"LEFT-{moment}-natural-pv_back", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("back", eye="left"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"LEFT-{moment}-natural-pv_left", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("left", eye="left"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"LEFT-{moment}-natural-pv_right", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("right", eye="left"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"LEFT-{moment}-natural-pv_top", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("top", eye="left"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"LEFT-{moment}-natural-pv_bottom", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("bottom", eye="left"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)

moment = False
render(f"LEFT-{moment}-natural-pv_front", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("front", eye="left"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"LEFT-{moment}-natural-pv_back", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("back", eye="left"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"LEFT-{moment}-natural-pv_left", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("left", eye="left"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"LEFT-{moment}-natural-pv_right", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("right", eye="left"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"LEFT-{moment}-natural-pv_top", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("top", eye="left"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"LEFT-{moment}-natural-pv_bottom", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("bottom", eye="left"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)

# Right eye
moment = "D3T3"
render(f"RIGHT-{moment}-natural-pv_front", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("front", eye="right"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"RIGHT-{moment}-natural-pv_back", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("back", eye="right"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"RIGHT-{moment}-natural-pv_left", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("left", eye="right"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"RIGHT-{moment}-natural-pv_right", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("right", eye="right"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"RIGHT-{moment}-natural-pv_top", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("top", eye="right"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"RIGHT-{moment}-natural-pv_bottom", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("bottom", eye="right"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)

moment = False
render(f"RIGHT-{moment}-natural-pv_front", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("front", eye="right"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"RIGHT-{moment}-natural-pv_back", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("back", eye="right"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"RIGHT-{moment}-natural-pv_left", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("left", eye="right"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"RIGHT-{moment}-natural-pv_right", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("right", eye="right"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"RIGHT-{moment}-natural-pv_top", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("top", eye="right"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
render(f"RIGHT-{moment}-natural-pv_bottom", upscale=1, model = add_SXII_shapes, artificial_lighting_shape_generator = generate_C2_shapes, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = get_stereo_face("bottom", eye="right"), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)

print("Finished")

# Force cleanup of DrJit resources to avoid hanging
# dr.flush_malloc_cache()  # Clear memory cache
import gc
gc.collect()
# mi.shutdown()  # Shutdown DrJit explicitly (if applicable)
