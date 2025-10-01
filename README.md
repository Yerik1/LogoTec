# LogoTec

Repositorio del proyecto del curso de Compiladores e Interpretes II Semestre 2025


## Ejecutar el proyecto en IntelliJ IDEA

### 1. Abrir el proyecto
- En IntelliJ, selecciona **File → Open...** y abre la carpeta raíz del proyecto.
- IntelliJ detectará automáticamente el archivo `pom.xml` y te pedirá importarlo como proyecto **Maven**. Acepta.

### 2. Esperar la descarga de dependencias
- IntelliJ descargará automáticamente todas las librerías (incluyendo JavaFX) desde Maven Central.
- Esto puede tardar la primera vez.

### 3. Configurar una Run Configuration con Maven
1. Ve a **Run → Edit Configurations...**.
2. Haz clic en **+** y selecciona **Maven**.
3. En **Working directory**, selecciona la carpeta raíz del proyecto.
4. En **Command line**, escribe:
   ```bash
   clean javafx:run
    ```
5. Dale un nombre (por ejemplo: Run JavaFX).
6. Guarda la configuración.

### 4. Ejecutar la aplicación
- Selecciona la configuración Run JavaFX en la esquina superior derecha de IntelliJ.
- Haz clic en el botón Run ▶ (o presiona Shift+F10).
- La aplicación JavaFX debería iniciar sin necesidad de configuraciones adicionales.