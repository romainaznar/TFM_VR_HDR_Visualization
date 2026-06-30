precision highp float;

uniform sampler2D tSATAtlasLeft;
uniform sampler2D tSATAtlasRight;
uniform float uFaceHeight;

uniform vec2 uLocalMinUV[6];
uniform vec2 uLocalMaxUV[6];

uniform vec2 uGlobalMinUV[6];
uniform vec2 uGlobalMaxUV[6];

uniform sampler2D tPreviousAdaptation;
uniform float uDeltaTime;

const float TAU_LIGHT = 1.0; 
const float TAU_DARK = 2.0; 

float summedAreaTable(sampler2D sat, vec2 minUV, vec2 maxUV) {
  float A = texture(sat, minUV).r;
  float B = texture(sat, vec2(maxUV.x, minUV.y)).r;
  float C = texture(sat, vec2(minUV.x, maxUV.y)).r;
  float D = texture(sat, maxUV).r;

  float sum = D - B - C + A;

  return sum;
}

vec2 faceUVToAtlasUV(int faceIndex, vec2 faceUV) {
  float faceWidth = 1.0 / 6.0;

  float texelX = 0.5 / (uFaceHeight * 6.0);
  float texelY = 0.5 / uFaceHeight;

  float atlasU = (float(faceIndex) + faceUV.x) * faceWidth;

  atlasU = clamp(atlasU, float(faceIndex) * faceWidth + texelX,
                 (float(faceIndex) + 1.0) * faceWidth - texelX);

  float atlasV = clamp(faceUV.y, texelY, 1.0 - texelY);

  return vec2(atlasU, atlasV);
}

void main() {
  float sumLuminanceLeft = 0.0;
  float sumLuminanceRight = 0.0;
  float totalArea = 0.0;

  for (int i = 0; i < 6; i++) {
    vec2 minUV = uLocalMinUV[i];
    vec2 maxUV = uLocalMaxUV[i];

    float area =
        uFaceHeight * uFaceHeight * (maxUV.x - minUV.x) * (maxUV.y - minUV.y);

    if (area <= 0.0) {
      continue;
    }

    totalArea += area;

    minUV = faceUVToAtlasUV(i, minUV);
    maxUV = faceUVToAtlasUV(i, maxUV);

    sumLuminanceLeft += summedAreaTable(tSATAtlasLeft, minUV, maxUV);
    sumLuminanceRight += summedAreaTable(tSATAtlasRight, minUV, maxUV);
  }

  float targetLocalLuminance =
      (sumLuminanceLeft + sumLuminanceRight) * 0.5 / totalArea;

  sumLuminanceLeft = 0.0;
  sumLuminanceRight = 0.0;
  totalArea = 0.0;

  for (int i = 0; i < 6; i++) {
    vec2 minUV = uGlobalMinUV[i];
    vec2 maxUV = uGlobalMaxUV[i];

    float area =
        uFaceHeight * uFaceHeight * (maxUV.x - minUV.x) * (maxUV.y - minUV.y);

    if (area <= 0.0) {
      continue;
    }

    totalArea += area;

    minUV = faceUVToAtlasUV(i, minUV);
    maxUV = faceUVToAtlasUV(i, maxUV);

    sumLuminanceLeft += summedAreaTable(tSATAtlasLeft, minUV, maxUV);
    sumLuminanceRight += summedAreaTable(tSATAtlasRight, minUV, maxUV);
  }

  float targetGlobalLuminance =
      (sumLuminanceLeft + sumLuminanceRight) * 0.5 / totalArea;

  vec2 prevAdaptation = texture(tPreviousAdaptation, vec2(0.5)).rg;
  float prevLocal = prevAdaptation.r;
  float prevGlobal = prevAdaptation.g;

  float tauGlobal = (targetGlobalLuminance > prevGlobal) ? TAU_LIGHT : TAU_DARK;
  float adaptedGlobal = prevGlobal + (targetGlobalLuminance - prevGlobal) *
                                         (1.0 - exp(-uDeltaTime / tauGlobal));

  float tauLocal = (targetLocalLuminance > prevLocal) ? TAU_LIGHT : TAU_DARK;
  float adaptedLocal = prevLocal + (targetLocalLuminance - prevLocal) *
                                       (1.0 - exp(-uDeltaTime / tauLocal));

  gl_FragColor = vec4(adaptedLocal, adaptedGlobal, 0.0, 1.0);
}