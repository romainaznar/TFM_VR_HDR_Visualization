precision highp float;

uniform samplerCube tCubeMapLeft;
uniform samplerCube tCubeMapRight;
uniform int uEye;

uniform int uToneMapping;
uniform sampler2D tAdaptation;
uniform float uExposure;

varying vec3 vPosition;

vec3 ReinhardToneMapping(vec3 color, float exposure, float whitePoint) {
  color *= exposure;

  vec3 whitePointSq = vec3(whitePoint * whitePoint);

  vec3 numerator = color * (vec3(1.0) + (color / whitePointSq));
  vec3 denominator = vec3(1.0) + color;

  return numerator / denominator;
}

vec3 ACESFilmicToneMapping(vec3 color, float exposure) {
  color *= exposure;

  float a = 2.51;
  float b = 0.03;
  float c = 2.43;
  float d = 0.59;
  float e = 0.14;
  return clamp((color * (a * color + b)) / (color * (c * color + d) + e), 0.0,
               1.0);
}

vec3 HVSToneMapping(vec3 color) {
  float scalingFactor = 10000.0;

  float localLuminance = texture(tAdaptation, vec2(0.5, 0.5)).r;
  float globalLuminance = texture(tAdaptation, vec2(0.5, 0.5)).g;

  float safeGlobal = max(globalLuminance, 1e-7);
  float safeLocal = max(localLuminance, 1e-7);
  float logRatio = log2(safeLocal / safeGlobal);
  float compressedRatio = tanh(logRatio * 0.8);

  float blendedLuminance = safeGlobal * exp2(compressedRatio * 0.8);

  float scaledBlendedLuminance = blendedLuminance * scalingFactor;

  float luminance = dot(color, vec3(0.2126, 0.7152, 0.0722));
  float scaledLuminance = luminance * scalingFactor;

  if (scaledBlendedLuminance < 8.0) {
    float rodContribution =
        clamp((8.0 - scaledBlendedLuminance) / 8.0, 0.0, 1.0);
    float rodLuminance = dot(color, vec3(0.0, 0.6, 0.4));

    vec3 purkinjeTint = vec3(0.75, 0.85, 1.15);
    vec3 blueShiftedColor = vec3(rodLuminance) * purkinjeTint;

    color = mix(color, blueShiftedColor, rodContribution);
  }

  float exposure = 1.5 / pow(max(blendedLuminance, 1e-7), 0.6);
  exposure = clamp(exposure, 0.05, 1000.0);

  float contrastAdjustment =
      log(max(scaledBlendedLuminance, 1.0)) / 2.0 * log(10.0);
  float whitePoint = 7.0 + contrastAdjustment;

  float huntEffect = pow(max(scaledBlendedLuminance, 1e-7) / 100.0, 0.05);
  huntEffect = clamp(huntEffect, 0.9, 1.1);

  color = mix(vec3(luminance), color, huntEffect);

  float mappedLuminance =
      ReinhardToneMapping(vec3(luminance), exposure, whitePoint).r;

  return (color / max(luminance, 1e-7)) * mappedLuminance;
}

void main() {
  vec3 dir = normalize(vPosition);
  dir.y *= -1.0;
  dir.z *= -1.0;
  vec3 color;
  if (uEye == 0) {
    color = texture(tCubeMapLeft, dir).rgb;
  } else {
    color = texture(tCubeMapRight, dir).rgb;
  }

  if (uToneMapping == 0) {
    color = ReinhardToneMapping(color, uExposure, 4.0);
  } else if (uToneMapping == 1) {
    color = ACESFilmicToneMapping(color, uExposure);
  } else if (uToneMapping == 2) {
    color = HVSToneMapping(color);
  }

  color = pow(color, vec3(1.0 / 2.2));
  gl_FragColor = vec4(color, 1.0);
}
