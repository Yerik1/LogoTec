import javafx.application.Application;
import javafx.scene.Scene;
import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.stage.Stage;

public class LogoTecIDE extends Application {

    private TextArea codeArea;     // Editor de código LogoTec
    private TextArea outputArea;   // Errores y warnings
    private Canvas canvas;         // Zona de dibujo (tortuga)

    @Override
    public void start(Stage stage) {
        // --- Zona de edición de código ---
        codeArea = new TextArea();
        codeArea.setPromptText("// Escribe tu programa LogoTec aquí...");

        // --- Zona de salida (errores/compilación) ---
        outputArea = new TextArea();
        outputArea.setEditable(false);
        outputArea.setPrefHeight(120);

        // --- Zona de dibujo (Canvas para la tortuga) ---
        canvas = new Canvas(400, 400);
        GraphicsContext gc = canvas.getGraphicsContext2D();
        gc.strokeText("Zona de dibujo - Tortuga", 120, 200);

        // --- Botones principales ---
        Button compileBtn = new Button("Compilar");
        compileBtn.setOnAction(e -> compileCode());

        Button astBtn = new Button("Mostrar AST");
        astBtn.setOnAction(e -> showAST());

        Button runBtn = new Button("Ejecutar");
        runBtn.setOnAction(e -> runProgram());

        Button loadBtn = new Button("Cargar archivo");
        loadBtn.setOnAction(e -> loadFile());

        HBox buttonBar = new HBox(10, loadBtn, compileBtn, astBtn, runBtn);

        // --- Layout principal ---
        SplitPane splitPane = new SplitPane(codeArea, canvas);
        splitPane.setDividerPositions(0.5);

        BorderPane root = new BorderPane();
        root.setTop(buttonBar);
        root.setCenter(splitPane);
        root.setBottom(outputArea);

        // --- Ventana principal ---
        stage.setScene(new Scene(root, 900, 600));
        stage.setTitle("LogoTec IDE - FrontEnd");
        stage.show();
    }

    // Métodos para conectar con tu compilador
    private void compileCode() {
        String code = codeArea.getText();
        // Aquí llamás a tu analizador/compilador
        outputArea.setText("Compilando...\n(Sin lógica conectada aún)");
    }

    private void showAST() {
        // Aquí deberías generar y mostrar el AST con tu compilador
        Alert astWindow = new Alert(Alert.AlertType.INFORMATION);
        astWindow.setHeaderText("Árbol Sintáctico Abstracto");
        astWindow.setContentText("(Aquí se mostrará el AST)");
        astWindow.showAndWait();
    }

    private void runProgram() {
        // Aquí simulás la ejecución del archivo objeto en el canvas
        outputArea.appendText("\nEjecutando programa...\n");
    }

    private void loadFile() {
        // Aquí implementás lógica para cargar un archivo fuente LogoTec
        outputArea.appendText("\nCargar archivo aún no implementado.\n");
    }

    public static void main(String[] args) {
        launch(args);
    }
}
