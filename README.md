# 🚗 Intelligent Geometric Identification System (Heatstakes)
> **Automated detection of geometric features in automotive CAD models.** > *A collaboration between UAEMéx and General Motors.*

[![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Completed-success)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

---

## 📖 Table of Contents / Tabla de Contenidos
1. [English Version](#-english-version)
    - [About the Project](#about-the-project)
    - [Key Features](#key-features)
    - [Tech Stack](#tech-stack)
    - [Installation](#installation)
    - [Usage](#usage)
    - [Project Structure](#project-structure)
    - [The Team](#the-team)
2. [Versión en Español](#-versión-en-español)
    - [Sobre el Proyecto](#sobre-el-proyecto)
    - [Características Principales](#características-principales)
    - [Tecnologías](#tecnologías)
    - [Instalación](#instalación)
    - [Uso](#uso)
    - [Estructura del Proyecto](#estructura-del-proyecto)
    - [El Equipo](#el-equipo)

---

# 🇺🇸 English Version

## About the Project
This project was developed as part of the **Applied Engineering Challenge** between the **Autonomous University of the State of Mexico (UAEMéx)** and **General Motors (GM)**.

The goal was to create a standalone software tool capable of processing complex automotive **STEP files (CAD)** to automatically identify specific geometric features known as **Heatstakes** (hollow cylindrical mounting posts). The system differentiates these features from similar geometries (like Waydoors or Locators) and calculates their precise **Center of Gravity (CoG)**, exporting the data for Manufacturing and Quality Assurance purposes.

## Key Features
* **🚀 GUI Launcher:** User-friendly interface built with Tkinter; no coding knowledge required.
* **🧠 Intelligent Filtering:** Uses Topological Analysis and Clustering (DBSCAN) to distinguish heatstakes from noise.
* **🧊 3D Visualization:** Interactive viewer based on `pythonocc` with a layering system to inspect results.
* **📊 Automated Reporting:** Generates Excel (`.xlsx`) and Text (`.txt`) reports with precise (X, Y, Z) coordinates.
* **⚡ High Performance:** Reduces inspection time from minutes (manual) to ~15-30 seconds per part.

## Tech Stack
* **Language:** Python 3.10+
* **Core Logic:** `pythonocc-core` (Geometric Kernel), `numpy`
* **Analysis/AI:** `scikit-learn` (DBSCAN Clustering), `pandas`
* **GUI:** `tkinter` (Standard Python GUI)
* **Visualization:** `pythonocc` (AIS, Display, OpenCascade kernel)

## Installation

### Prerequisites
* [Anaconda](https://www.anaconda.com/) or Miniconda (Recommended for managing CAD libraries).

### Steps
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/EnriqueMAP/HeatStakesDetectionGM.git](https://github.com/EnriqueMAP/HeatStakesDetectionGM.git)
    cd HeatStakesDetectionGM
    ```

2.  **Create the environment:**
    ```bash
    conda create -n heatstakes-env python=3.10
    conda activate heatstakes-env
    ```

3.  **Install dependencies:**
    ```bash
    conda install -c conda-forge pythonocc-core=7.7.0
    pip install pandas scikit-learn openpyxl
    ```

## Usage
1.  Activate your environment: `conda activate heatstakes-env`
2.  Run the launcher:
    ```bash
    python app_gui.py
    ```
3.  **In the GUI:**
    * Click **"Buscar"** to select a `.stp` file.
    * (Optional) Check "Ver en 3D" or "Fusión de Familias".
    * Click **"EJECUTAR"**.
4.  **Results:** Check the `Reportes/` folder created in the root directory.

## Project Structure
HeatStakesDetectionGM/
│
├── app_gui.py
│   # Main application entry point.
│   # Launches the graphical user interface.
│
├── run_process.py
│   # Background worker responsible for heavy geometric processing.
│   # Prevents UI blocking during analysis.
│
├── src/
│   # Core logic and processing modules
│   │
│   ├── geometry.py
│   # STEP file loading and topology extraction
│   │
│   ├── analyzer.py
│   # Geometric filtering and DBSCAN-based clustering
│   │
│   ├── visualizer.py
│   # 3D visualization logic and interaction menus
│   │
│   └── family_merger.py
│   # Logic for merging geometrically related or split faces
│
└── Reportes/
    # Generated output files (ignored by git)

## 🔮 Future Work & Recommendations

While the current system fulfills the original project objectives, several extensions could further enhance its industrial applicability and scalability:

### 📦 Packaging
- Convert the tool into a standalone executable (`.exe`)
- Simplify deployment on plant PCs without requiring a Python environment

### 📈 Scalability
- Extend geometric analysis to detect additional features:
  - Clips
  - Screws
  - Weld points
  - Other fastening elements

### 🗂️ Batch Processing
- Enable automatic analysis of entire folders
- Support hundreds of STEP files per execution
- Improve throughput for large-scale inspections

## The Team
**Lead Developers & Researchers:**
* Miguel Ángel Aguilar Díaz
* Kárilyn A. Orozco Morales
* Emmanuel García Nateras
* Enrique Molina Aguilar
* Aldo Jareth García Muciño
* José Pablo Sánchez Sánchez
* Juan Carlos Escamilla Vargas
* Eduardo Adán Flores Estrada

**Advisors:**
* **Academic:** José Luis Núñez Mejía
* **Industrial:** General Motors Engineering Liaison

---

# 🇲🇽 Versión en Español

## Sobre el Proyecto
Este proyecto fue desarrollado como parte del **Reto de Ingeniería Aplicada** entre la **Universidad Autónoma del Estado de México (UAEMéx)** y **General Motors (GM)**.

El objetivo fue crear una herramienta de software independiente capaz de procesar archivos **STEP (CAD)** automotrices complejos para identificar automáticamente características geométricas específicas llamadas **Heatstakes** (postes de sujeción cilíndricos). El sistema diferencia estos elementos de geometrías similares (como Waydoors o Locators) y calcula su **Centro de Gravedad (CoG)** preciso, exportando los datos para las áreas de Manufactura y Calidad.

## Características Principales
* **🚀 Launcher Gráfico:** Interfaz amigable construida con Tkinter; no requiere saber programar.
* **🧠 Filtrado Inteligente:** Utiliza Análisis Topológico y Clustering (DBSCAN) para separar los heatstakes del "ruido".
* **🧊 Visualización 3D:** Visor interactivo basado en `pythonocc` con sistema de capas para inspección.
* **📊 Reportes Automáticos:** Genera reportes en Excel (`.xlsx`) y Texto (`.txt`) con coordenadas (X, Y, Z).
* **⚡ Alto Rendimiento:** Reduce el tiempo de inspección de minutos (manual) a ~15-30 segundos por pieza.

## Tecnologías
* **Lenguaje:** Python 3.10+
* **Lógica Núcleo:** `pythonocc-core` (Kernel Geométrico), `numpy`
* **Análisis/IA:** `scikit-learn` (DBSCAN Clustering), `pandas`
* **Interfaz (GUI):** `tkinter`
* **Visualización:** `pythonocc` (AIS, Display, OpenCascade kernel)

## Instalación

### Requisitos Previos
* [Anaconda](https://www.anaconda.com/) o Miniconda (Recomendado para manejar librerías CAD).

### Pasos
1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/EnriqueMAP/HeatStakesDetectionGM.git](https://github.com/EnriqueMAP/HeatStakesDetectionGM.git)
    cd HeatStakesDetectionGM
    ```

2.  **Crear el entorno:**
    ```bash
    conda create -n heatstakes-env python=3.10
    conda activate heatstakes-env
    ```

3.  **Instalar dependencias:**
    ```bash
    conda install -c conda-forge pythonocc-core=7.7.0
    pip install pandas scikit-learn openpyxl
    ```

## Uso
1.  Activa tu entorno: `conda activate heatstakes-env`
2.  Ejecuta el launcher:
    ```bash
    python app_gui.py
    ```
3.  **En la Interfaz:**
    * Clic en **"Buscar"** para seleccionar un archivo `.stp`.
    * (Opcional) Marca "Ver en 3D" o "Fusión de Familias".
    * Clic en **"EJECUTAR"**.
4.  **Resultados:** Revisa la carpeta `Reportes/` que se crea automáticamente.

## Estructura del Proyecto
HeatStakesDetectionGM/
│
├── app_gui.py
│   # Punto de entrada principal.
│   # Lanza la interfaz gráfica del sistema.
│
├── run_process.py
│   # Proceso en segundo plano encargado del análisis geométrico.
│   # Evita bloqueos en la interfaz.
│
├── src/
│   # Módulos de lógica interna y procesamiento
│   │
│   ├── geometry.py
│   # Carga de archivos STEP y extracción topológica
│   │
│   ├── analyzer.py
│   # Filtrado geométrico y clustering mediante DBSCAN
│   │
│   ├── visualizer.py
│   # Visualización 3D e interacción con el modelo
│   │
│   └── family_merger.py
│   # Lógica para unir caras geométricamente relacionadas
│
└── Reportes/
    # Archivos generados (ignorados por git)

## 🔮 Trabajo Futuro y Recomendaciones

Aunque el sistema actual cumple con los objetivos planteados inicialmente, existen extensiones que pueden incrementar su aplicabilidad industrial:

### 📦 Empaquetado
- Convertir la herramienta en un ejecutable independiente (`.exe`)
- Facilitar la instalación en computadoras de planta sin entorno Python

### 📈 Escalabilidad
- Ampliar el análisis geométrico para detectar:
  - Clips
  - Tornillos
  - Puntos de soldadura
  - Otros elementos de fijación

### 🗂️ Procesamiento por Lotes
- Análisis automático de carpetas completas
- Soporte para cientos de archivos STEP por ejecución
- Mayor eficiencia en inspecciones masivas

## El Equipo
**Desarrolladores e Investigadores:**
* Miguel Ángel Aguilar Díaz
* Kárilyn A. Orozco Morales
* Emmanuel García Nateras
* Enrique Molina Aguilar
* Aldo Jareth García Muciño
* José Pablo Sánchez Sánchez
* Juan Carlos Escamilla Vargas
* Eduardo Adán Flores Estrada

**Asesores:**
* **Académico:** José Luis Núñez Mejía
* **Industrial:** Enlace de Ingeniería General Motors

---
© 2025 UAEMéx / General Motors Collaboration.