# TFM Project: Rendering, VR visualization and perceptual evaluation of HDR renders of cultural heritage sites

This is the repository for the TFM project "Rendering, VR visualization and perceptual evaluation of HDR renders of cultural heritage sites", a project developed by Romain Aznar and supervised by Imanol Muñoz-Pandiella and Carlos Andújar at the Universitat Politècnica de Catalunya (UPC). The project focuses on the rendering and visualization of cultural heritage sites in VR using HDR techniques.

## Prerequisites

Before running the project, ensure your system meets the following requirements:

- Python 3.x installed on your system
- Node.js and npm
- A compatible VR headset for WebXR

## Project Structure

- `rendering/`: Contains the Python Mitsuba renderer for the HDR cube map rendering of the Sant Quirze de Pedret church, a project originally developed by Imanol Muñoz-Pandiella and Carlos Andújar, and adapted for this project specific needs. You can explore the [original project on GitHub](https://github.com/UPC-ViRVIG/MuralLighting).
- `summed-area-tables/`: Contains the Summed Area Tables (SAT) atlas generator from the cube map faces.
- `webapp/`: Contains the Three.js web application for the visualization of the scene in VR, with custom shaders implementing different TMOs, including one approximation of some characteristics of the Human Visual System.

## Execution Instructions

**Note:** The repository already includes a set of pre-rendered cube map faces and the corresponding SAT atlas in `webapp/textures/`, so you can run the web application directly without completing the rendering steps. If you want to use your own renders instead, follow the instructions below.

### Rendering

To render the HDR cube map of the Sant Quirze de Pedret church, follow these steps:

1. Navigate to the `rendering/` directory.
2. Install the required dependencies for Python from the `requirements.txt` file.
3. Run the rendering script to generate the HDR cube map with this command:

   ```bash
   python code/final/distant-refactorized.py
   ```

**Note:** The rendering was performed on a Linux environment with a NVIDIA GPU and the latest NVIDIA drivers installed. If your system has different specifications, you may need to adjust the rendering parameters accordingly. The rendering process can take a significant amount of time depending on your hardware capabilities.

### Summed Area Tables (SAT) Generation

To generate the Summed Area Tables (SAT) atlas from the rendered cube map faces, follow these steps:

1. Navigate to the `summed-area-tables/` directory.
2. Install the required dependencies for Python from the `requirements.txt` file.
3. Paste the rendered cube map faces into the directory without changing their names.
4. Run the SAT generation script with this command:

   ```bash
   python main.py
   ```

### Web Application
To visualize the HDR renders in VR using the Three.js web application, follow these steps:

1. Navigate to the `webapp/` directory.
2. Run `npm install` to install the required dependencies.
3. The repository already includes a set of pre-rendered cube map faces and the corresponding SAT atlas in `webapp/textures/`, so you can run the application directly without completing the previous steps. If you want to use your own renders instead, paste the generated cube map faces and the SAT atlas into the `webapp/textures/` directory without changing their names, overwriting the existing files.
4. Start the web application with the following command:

   ```bash
   npm start
   ```
5. Open your web browser and navigate to `http://127.0.0.1:8080` to access the VR visualization of the HDR renders.

You can then explore the scene in VR by clicking the "Enter VR" button in the web application. Make sure you are accessing the application from a WebXR compatible device.
You can switch between different TMOs and environments using the provided interface in the web application to evaluate the perceptual differences in the HDR renders. There also is a slider to adjust the exposure of the scene for the global TMOs implemented.