import * as THREE from 'three';

import { EXRLoader } from 'three/addons/loaders/EXRLoader.js';
import { VRButton } from 'three/addons/webxr/VRButton.js';
import { GUI } from 'three/addons/libs/lil-gui.module.min.js';
import { HTMLMesh } from 'three/addons/interactive/HTMLMesh.js';
import { InteractiveGroup } from 'three/addons/interactive/InteractiveGroup.js';
import { XRControllerModelFactory } from 'three/addons/webxr/XRControllerModelFactory.js';
import Stats from 'three/addons/libs/stats.module.js';

const skyVertexShader = await (await fetch('./shaders/sky.vert')).text();
const skyFragmentShader = await (await fetch('./shaders/sky.frag')).text();

const adaptationVertexShader = await (await fetch('./shaders/adaptation.vert')).text();
const adaptationFragmentShader = await (await fetch('./shaders/adaptation.frag')).text();

const shaderSettings = {
	toneMapping: 2,
	exposureStops: 0.0,
	environnement: 0
};

const timer = new THREE.Timer();

let camera;
let renderer;
let scene;
let skyBox;
let stats;

let leftDayTextures = [];
let rightDayTextures = [];
let leftNightTextures = [];
let rightNightTextures = [];

let leftDaySATTexture;
let rightDaySATTexture;
let leftNightSATTexture;
let rightNightSATTexture;

let adaptationMaterial;
let adaptationScene;
let currentAdaptationTarget;
let previousAdaptationTarget;

init();

function init() {
	const container = document.getElementById('container');

	renderer = new THREE.WebGLRenderer();

	renderer.xr.enabled = true;
	renderer.toneMapping = THREE.NoToneMapping;
	renderer.outputColorSpace = THREE.SRGBColorSpace;
	renderer.setPixelRatio(window.devicePixelRatio);
	renderer.setSize(window.innerWidth, window.innerHeight);
	renderer.setAnimationLoop(animate);
	container.appendChild(renderer.domElement);
	document.body.appendChild(VRButton.createButton(renderer));

	stats = new Stats();
    document.body.appendChild(stats.dom);

	scene = new THREE.Scene();

	camera = new THREE.PerspectiveCamera(90, window.innerWidth / window.innerHeight, 0.1, 100);

	const leftDayFaceUrls = [
		'textures/LEFT-D3T3-natural-pv_right.exr',
		'textures/LEFT-D3T3-natural-pv_left.exr',
		'textures/LEFT-D3T3-natural-pv_bottom.exr',
		'textures/LEFT-D3T3-natural-pv_top.exr',
		'textures/LEFT-D3T3-natural-pv_front.exr',
		'textures/LEFT-D3T3-natural-pv_back.exr'
	];
	const rightDayFaceUrls = [
		'textures/RIGHT-D3T3-natural-pv_right.exr',
		'textures/RIGHT-D3T3-natural-pv_left.exr',
		'textures/RIGHT-D3T3-natural-pv_bottom.exr',
		'textures/RIGHT-D3T3-natural-pv_top.exr',
		'textures/RIGHT-D3T3-natural-pv_front.exr',
		'textures/RIGHT-D3T3-natural-pv_back.exr'
	];
	const leftNightFaceUrls = [
		'textures/LEFT-False-natural-pv_right.exr',
		'textures/LEFT-False-natural-pv_left.exr',
		'textures/LEFT-False-natural-pv_bottom.exr',
		'textures/LEFT-False-natural-pv_top.exr',
		'textures/LEFT-False-natural-pv_front.exr',
		'textures/LEFT-False-natural-pv_back.exr'
	];
	const rightNightFaceUrls = [
		'textures/RIGHT-False-natural-pv_right.exr',
		'textures/RIGHT-False-natural-pv_left.exr',
		'textures/RIGHT-False-natural-pv_bottom.exr',
		'textures/RIGHT-False-natural-pv_top.exr',
		'textures/RIGHT-False-natural-pv_front.exr',
		'textures/RIGHT-False-natural-pv_back.exr'
	];

	const leftDaySATAtlasUrl = 'textures/LEFT-D3T3-natural-pv_sat_atlas.exr';
	const rightDaySATAtlasUrl = 'textures/RIGHT-D3T3-natural-pv_sat_atlas.exr';
	const leftNightSATAtlasUrl = 'textures/LEFT-False-natural-pv_sat_atlas.exr';
	const rightNightSATAtlasUrl = 'textures/RIGHT-False-natural-pv_sat_atlas.exr';

	Promise.all([
		getCubeMapFromFiles(leftDayFaceUrls, 6),
		getCubeMapFromFiles(rightDayFaceUrls, 6),
		getCubeMapFromFiles(leftNightFaceUrls, 6),
		getCubeMapFromFiles(rightNightFaceUrls, 6),
		loadSingleEXR(leftDaySATAtlasUrl),
		loadSingleEXR(rightDaySATAtlasUrl),
		loadSingleEXR(leftNightSATAtlasUrl),
		loadSingleEXR(rightNightSATAtlasUrl)
	]).then(([loadedLeftDayCube, loadedRightDayCube, loadedLeftNightCube, loadedRightNightCube, loadedLeftDaySAT, loadedRightDaySAT, loadedLeftNightSAT, loadedRightNightSAT]) => {
		leftDayTextures = loadedLeftDayCube;
		rightDayTextures = loadedRightDayCube;
		leftNightTextures = loadedLeftNightCube;
		rightNightTextures = loadedRightNightCube;
		leftDaySATTexture = loadedLeftDaySAT;
		rightDaySATTexture = loadedRightDaySAT;
		leftNightSATTexture = loadedLeftNightSAT;
		rightNightSATTexture = loadedRightNightSAT;

		currentAdaptationTarget = new THREE.WebGLRenderTarget(1, 1, {
			type: THREE.FloatType,
			minFilter: THREE.NearestFilter,
			magFilter: THREE.NearestFilter
		});
		previousAdaptationTarget = currentAdaptationTarget.clone();

		const skyMaterial = new THREE.ShaderMaterial({
			vertexShader: skyVertexShader,
			fragmentShader: skyFragmentShader,
			uniforms: {
				tCubeMapLeft: { value: leftDayTextures },
				tCubeMapRight: { value: rightDayTextures },
				uEye: { value: 0 },
				uToneMapping: { value: shaderSettings.toneMapping },
				tAdaptation: { value: currentAdaptationTarget.texture },
				uExposure: { value: Math.pow(2.0, shaderSettings.exposureStops) }
			},
			side: THREE.BackSide,
		});

		adaptationMaterial = new THREE.ShaderMaterial({
			vertexShader: adaptationVertexShader,
			fragmentShader: adaptationFragmentShader,
			uniforms: {
				tSATAtlasLeft: { value: leftDaySATTexture },
				tSATAtlasRight: { value: rightDaySATTexture },
				uFaceHeight: { value: leftDaySATTexture.image.height },
				uLocalMinUV: { value: Array.from({ length: 6 }, () => new THREE.Vector2()) },
				uLocalMaxUV: { value: Array.from({ length: 6 }, () => new THREE.Vector2()) },
				uGlobalMinUV: { value: Array.from({ length: 6 }, () => new THREE.Vector2()) },
				uGlobalMaxUV: { value: Array.from({ length: 6 }, () => new THREE.Vector2()) },
				tPreviousAdaptation: { value: null },
				uDeltaTime: { value: 0.0 }
			},
			depthWrite: false,
			depthTest: false
		});

		adaptationScene = new THREE.Scene();

		const adaptationMesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), adaptationMaterial);
		adaptationMesh.frustumCulled = false;
		adaptationScene.add(adaptationMesh);

		skyBox = new THREE.Mesh(new THREE.BoxGeometry(100, 100, 100), skyMaterial);

		skyBox.onBeforeRender = (renderer, scene, camera) => {
			if (camera.viewport) {
				const xrCam = renderer.xr.getCamera();
				const left = xrCam.cameras[0];

				skyBox.material.uniforms.uEye.value = (camera === left) ? 0 : 1;
			}
		};
		scene.add(skyBox);

		console.log('EXR textures loaded successfully.');
	}).catch((err) => {
		console.error('Error loading EXR textures:', err);
	});

	initGUI();

	window.addEventListener('resize', onWindowResize);
}

function updateShaderUniforms() {
	if (skyBox && skyBox.material) {
		const linearExposure = Math.pow(2.0, shaderSettings.exposureStops);

		skyBox.material.uniforms.uToneMapping.value = shaderSettings.toneMapping;
		skyBox.material.uniforms.uExposure.value = linearExposure;

		skyBox.material.uniforms.tCubeMapLeft.value = shaderSettings.environnement === 0 ? leftDayTextures : leftNightTextures;
		skyBox.material.uniforms.tCubeMapRight.value = shaderSettings.environnement === 0 ? rightDayTextures : rightNightTextures;

		adaptationMaterial.uniforms.tSATAtlasLeft.value = shaderSettings.environnement === 0 ? leftDaySATTexture : leftNightSATTexture;
		adaptationMaterial.uniforms.tSATAtlasRight.value = shaderSettings.environnement === 0 ? rightDaySATTexture : rightNightSATTexture;
	}
}

function initGUI() {
	const gui = new GUI({ title: 'Shader Settings' });

	const toneFolder = gui.addFolder('Tone Mapping');

	toneFolder.add({
		Reinhard() {
			shaderSettings.toneMapping = 0;
			updateShaderUniforms();
		}
	}, 'Reinhard');

	toneFolder.add({
		ACESFilmic() {
			shaderSettings.toneMapping = 1;
			updateShaderUniforms();
		}
	}, 'ACESFilmic');

	toneFolder.add({
		HVS() {
			shaderSettings.toneMapping = 2;
			updateShaderUniforms();
		}
	}, 'HVS');

	gui.add(shaderSettings, 'exposureStops', -10, 10, 0.2)
		.name('Exposure')
		.onChange(() => {
			updateShaderUniforms();
		});

	const envFolder = gui.addFolder('Environment');

	envFolder.add({
		Day() {
			shaderSettings.environnement = 0;
			updateShaderUniforms();
		}
	}, 'Day');

	envFolder.add({
		Night() {
			shaderSettings.environnement = 1;
			updateShaderUniforms();
		}
	}, 'Night');

	const geometry = new THREE.BufferGeometry();
	geometry.setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, - 5)]);

	const controller1 = renderer.xr.getController(0);
	controller1.add(new THREE.Line(geometry));
	scene.add(controller1);

	const controller2 = renderer.xr.getController(1);
	controller2.add(new THREE.Line(geometry));
	scene.add(controller2);

	const controllerModelFactory = new XRControllerModelFactory();

	const controllerGrip1 = renderer.xr.getControllerGrip(0);
	controllerGrip1.add(controllerModelFactory.createControllerModel(controllerGrip1));
	scene.add(controllerGrip1);

	const controllerGrip2 = renderer.xr.getControllerGrip(1);
	controllerGrip2.add(controllerModelFactory.createControllerModel(controllerGrip2));
	scene.add(controllerGrip2);

	const group = new InteractiveGroup();
	group.listenToPointerEvents(renderer, camera);
	group.listenToXRControllerEvents(controller1);
	group.listenToXRControllerEvents(controller2);

	scene.add(group);

	const mesh = new HTMLMesh(gui.domElement);

	mesh.position.set(0.5, 1.5, -1.0);
	mesh.rotation.y = -0.15 * Math.PI;
	mesh.scale.setScalar(2);

	group.add(mesh);
}

async function getCubeMapFromFiles(urls) {
	const loader = new EXRLoader();

	const textures = await Promise.all(
		urls.map(url => new Promise((resolve, reject) => {
			loader.load(url, resolve, undefined, reject);
		}))
	);

	const cubeTex = new THREE.CubeTexture();

	cubeTex.images = textures;

	cubeTex.type = THREE.HalfFloatType;
	cubeTex.colorSpace = THREE.LinearSRGBColorSpace;
	cubeTex.needsUpdate = true;

	return cubeTex;
}

async function loadSingleEXR(url) {
	const loader = new EXRLoader();
	loader.setDataType(THREE.FloatType);
	return new Promise((resolve, reject) => {
		loader.load(url, (texture) => {
			texture.type = THREE.FloatType;
			texture.colorSpace = THREE.LinearSRGBColorSpace;
			resolve(texture);
		}, undefined, reject);
	});
}

function onWindowResize() {
	camera.aspect = window.innerWidth / window.innerHeight;
	camera.updateProjectionMatrix();

	renderer.setSize(window.innerWidth, window.innerHeight);
}

const faces = [
	{ face: 'left', dir: new THREE.Vector3(-1, 0, 0), up: new THREE.Vector3(0, 1, 0), right: new THREE.Vector3(0, 0, -1) },
	{ face: 'right', dir: new THREE.Vector3(1, 0, 0), up: new THREE.Vector3(0, 1, 0), right: new THREE.Vector3(0, 0, 1) },
	{ face: 'bottom', dir: new THREE.Vector3(0, -1, 0), up: new THREE.Vector3(0, 0, -1), right: new THREE.Vector3(1, 0, 0) },
	{ face: 'top', dir: new THREE.Vector3(0, 1, 0), up: new THREE.Vector3(0, 0, 1), right: new THREE.Vector3(1, 0, 0) },
	{ face: 'front', dir: new THREE.Vector3(0, 0, -1), up: new THREE.Vector3(0, 1, 0), right: new THREE.Vector3(1, 0, 0) },
	{ face: 'back', dir: new THREE.Vector3(0, 0, 1), up: new THREE.Vector3(0, 1, 0), right: new THREE.Vector3(-1, 0, 0) }
];

function getFaceIndex(dir) {
	const maxComponent = Math.max(Math.abs(dir.x), Math.abs(dir.y), Math.abs(dir.z));

	let faceIndex;
	if (maxComponent === Math.abs(dir.x)) {
		faceIndex = dir.x < 0 ? 0 : 1;
	} else if (maxComponent === Math.abs(dir.y)) {
		faceIndex = dir.y < 0 ? 2 : 3;
	} else {
		faceIndex = dir.z < 0 ? 4 : 5;
	}

	return faceIndex;
}

function directionToFaceUV(dir, faceIndex) {
	const faceDir = faces[faceIndex].dir;
	const upAxis = faces[faceIndex].up;
	const rightAxis = faces[faceIndex].right;

	const denom = dir.dot(faceDir);

	const u = dir.dot(rightAxis) / denom;
	const v = dir.dot(upAxis) / denom;

	return new THREE.Vector2(
		THREE.MathUtils.clamp((u + 1) * 0.5, 0, 1),
		THREE.MathUtils.clamp((v + 1) * 0.5, 0, 1)
	);
}

function getFaceMinMaxUV(dir, faceIndex, basis, angle, otherFaces) {
	const faceUp = faces[faceIndex].up;
	const faceDown = faceUp.clone().negate();
	const faceRight = faces[faceIndex].right;
	const faceLeft = faceRight.clone().negate();

	const tmp = new THREE.Vector3();

	let minU = Infinity, minV = Infinity, maxU = -Infinity, maxV = -Infinity;

	for (let i = 0; i < 128; i++) {
		const t = (i / 128) * Math.PI * 2;

		tmp.copy(dir)
			.multiplyScalar(Math.cos(angle))
			.addScaledVector(basis.right, Math.sin(angle) * Math.cos(t))
			.addScaledVector(basis.up, Math.sin(angle) * Math.sin(t))
			.normalize();

		const currentFaceIndex = getFaceIndex(tmp);
		if (currentFaceIndex !== faceIndex) {
			otherFaces.add(currentFaceIndex);
			continue;
		}

		const uv = directionToFaceUV(tmp, faceIndex);

		if (uv.x < minU) minU = uv.x;
		if (uv.x > maxU) maxU = uv.x;
		if (uv.y < minV) minV = uv.y;
		if (uv.y > maxV) maxV = uv.y;
	}

	otherFaces.forEach(otherFaceIndex => {
		if (faces[otherFaceIndex].dir.equals(faceLeft)) {
			minU = 0.0;
		} else if (faces[otherFaceIndex].dir.equals(faceRight)) {
			maxU = 1.0;
		} else if (faces[otherFaceIndex].dir.equals(faceDown)) {
			minV = 0.0;
		} else if (faces[otherFaceIndex].dir.equals(faceUp)) {
			maxV = 1.0;
		}
	});

	return {
		minUV: new THREE.Vector2(minU, minV),
		maxUV: new THREE.Vector2(maxU, maxV)
	};
}

function getFaceBounds(dir, mainFaceIndex, angle) {
	const faceBounds = [];
	const faceIndexes = new Set([mainFaceIndex]);

	const faceUpAxis = faces[mainFaceIndex].up;
	const rightAxis = new THREE.Vector3().crossVectors(dir, faceUpAxis).normalize();
	const upAxis = new THREE.Vector3().crossVectors(rightAxis, dir).normalize();
	const basis = { right: rightAxis, up: upAxis };

	const mainFaceBounds = getFaceMinMaxUV(dir, mainFaceIndex, basis, angle, faceIndexes);
	faceBounds[mainFaceIndex] = mainFaceBounds;

	const faceIndexesCopy = new Set(faceIndexes);
	faceIndexes.delete(mainFaceIndex);

	faceIndexes.forEach(faceIndex => {
		const bounds = getFaceMinMaxUV(dir, faceIndex, basis, angle, faceIndexesCopy);
		if (bounds.minUV.x < bounds.maxUV.x && bounds.minUV.y < bounds.maxUV.y) {
			faceBounds[faceIndex] = bounds;
		}
	});

	return faceBounds;
}

function getCubeMappings(radius) {
	const dir = new THREE.Vector3();
	camera.getWorldDirection(dir).normalize();
	const angle = THREE.MathUtils.degToRad(radius);

	const mainFaceIndex = getFaceIndex(dir);
	const faceBounds = getFaceBounds(dir, mainFaceIndex, angle);
	return faceBounds;
}

function animate() {
	if (!scene || !adaptationScene) {
		return;
	}

	if (stats) stats.update();

	timer.update();
	const deltaTime = timer.getDelta();
	adaptationMaterial.uniforms.uDeltaTime.value = deltaTime;

	for (let i = 0; i < 6; i++) {
		adaptationMaterial.uniforms.uLocalMinUV.value[i].set(0, 0);
		adaptationMaterial.uniforms.uLocalMaxUV.value[i].set(0, 0);
		adaptationMaterial.uniforms.uGlobalMinUV.value[i].set(0, 0);
		adaptationMaterial.uniforms.uGlobalMaxUV.value[i].set(0, 0);
	}

	const localFaceBounds = getCubeMappings(10.0);
	const globalFaceBounds = getCubeMappings(75.0);

	localFaceBounds.forEach((bounds, index) => {
		if (bounds) {
			adaptationMaterial.uniforms.uLocalMinUV.value[index] = bounds.minUV;
			adaptationMaterial.uniforms.uLocalMaxUV.value[index] = bounds.maxUV;
		}
	});
	globalFaceBounds.forEach((bounds, index) => {
		if (bounds) {
			adaptationMaterial.uniforms.uGlobalMinUV.value[index] = bounds.minUV;
			adaptationMaterial.uniforms.uGlobalMaxUV.value[index] = bounds.maxUV;
		}
	});

	adaptationMaterial.uniforms.tPreviousAdaptation.value = previousAdaptationTarget.texture;

	const currentTarget = renderer.getRenderTarget();

	const xrEnabled = renderer.xr.enabled;
	renderer.xr.enabled = false;

	renderer.setRenderTarget(currentAdaptationTarget);
	renderer.render(adaptationScene, camera);

	renderer.xr.enabled = xrEnabled;

	renderer.setRenderTarget(currentTarget);
	renderer.render(scene, camera);

	const temp = currentAdaptationTarget;
	currentAdaptationTarget = previousAdaptationTarget;
	previousAdaptationTarget = temp;
}