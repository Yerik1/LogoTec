// out/runtime.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#if defined(_WIN32)
  #ifndef WIN32_LEAN_AND_MEAN
  #define WIN32_LEAN_AND_MEAN
  #endif
  #ifndef NOMINMAX
  #define NOMINMAX
  #endif

  // 1) SIEMPRE incluir winsock2 antes que windows.h
  #include <winsock2.h>
  #include <ws2tcpip.h>

  // 2) Luego windows.h y resto
  #include <windows.h>
  #include <io.h>
  #include <fcntl.h>

  // 3) Link con Ws2_32 (necesario para sockets)
  #pragma comment(lib, "Ws2_32.lib")

  static void sleep_ms_os(int ms){ Sleep(ms); }
  #define PY_LAUNCH_FALLBACK "py.exe"
#endif

// ---------- getenv seguro ----------
static const char* getenv_safe(const char* name) {
#if defined(_WIN32)
    char* buf = NULL; size_t sz = 0;
    if (_dupenv_s(&buf, &sz, name) == 0 && buf && sz > 0) return buf; // liberar tras usar
    return NULL;
#else
    return getenv(name);
#endif
}

// ---------- log de depuración ----------
static void debug_log(const char* tag, const char* msg){
#if defined(_DEBUG) || 1
    fprintf(stderr, "[%s] %s\n", tag, msg);
    fflush(stderr);
#endif
}

// ---------- estado global ----------
//static FILE* g_py = NULL;
#if defined(_WIN32)
static SOCKET g_sock = INVALID_SOCKET; // embed TCP
#else
static int    g_sock = -1;
#endif
static FILE*  g_py   = NULL;

static void send_cmd(const char* s){
#if defined(_WIN32)
    if (g_sock != INVALID_SOCKET){
        int len = (int)strlen(s);
        send(g_sock, s, len, 0);
        send(g_sock, "\n", 1, 0);
        return;
    }
#else
    if (g_sock != -1){
        size_t len = strlen(s);
        send(g_sock, s, len, 0);
        send(g_sock, "\n", 1, 0);
        return;
    }
#endif
    if (g_py){ fputs(s, g_py); fputc('\n', g_py); fflush(g_py); }
}

// ==========================================================
// Lanzador específico de Windows (CreateProcess, sin shell)
// ==========================================================
#if defined(_WIN32)
static FILE* win_spawn_python(const char* exe_abs, const char* script_abs) {
    SECURITY_ATTRIBUTES sa; ZeroMemory(&sa, sizeof(sa));
    sa.nLength = sizeof(sa);
    sa.bInheritHandle = TRUE;
    sa.lpSecurityDescriptor = NULL;

    HANDLE hRead = NULL, hWrite = NULL;
    if (!CreatePipe(&hRead, &hWrite, &sa, 0)) {
        debug_log("rt_init", "CreatePipe failed");
        return NULL;
    }
    // Evitar que el extremo de escritura se herede por accidente:
    if (!SetHandleInformation(hWrite, HANDLE_FLAG_INHERIT, 0)) {
        debug_log("rt_init", "SetHandleInformation failed");
    }

    // Construye la línea de comandos:
    // "C:\...\python.exe" -u "C:\...\drawing.py"
    char cmdline[4096];
    if (exe_abs && exe_abs[0] && script_abs && script_abs[0]) {
        snprintf(cmdline, sizeof(cmdline), "\"%s\" -u \"%s\"", exe_abs, script_abs);
    } else if (script_abs && script_abs[0]) {
        // Fallback: py.exe -u "<script>"
        snprintf(cmdline, sizeof(cmdline), "%s -u \"%s\"", PY_LAUNCH_FALLBACK, script_abs);
    } else {
        debug_log("rt_init", "win_spawn_python: argumentos vacíos");
        CloseHandle(hRead); CloseHandle(hWrite);
        return NULL;
    }
    debug_log("rt_init", cmdline);

    STARTUPINFOA si; ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput  = hRead;            // stdin del hijo viene de nuestro pipe
    si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    si.hStdError  = GetStdHandle(STD_ERROR_HANDLE);

    PROCESS_INFORMATION pi; ZeroMemory(&pi, sizeof(pi));

    // Importante: ApplicationName = NULL → resolverá exe desde cmdline/Path
    BOOL ok = CreateProcessA(
        NULL,              // lpApplicationName
        cmdline,           // lpCommandLine (modificable)
        NULL, NULL,        // lpProcessAttributes, lpThreadAttributes
        TRUE,              // bInheritHandles (sí, para que reciba stdin)
        0,                 // dwCreationFlags
        NULL,              // lpEnvironment (hereda)
        NULL,              // lpCurrentDirectory (hereda nuestro cwd)
        &si, &pi
    );

    // Ya no necesitamos que el hijo herede el extremo de lectura en este proceso
    CloseHandle(hRead);

    if (!ok) {
        debug_log("rt_init", "CreateProcess failed");
        CloseHandle(hWrite);
        return NULL;
    }

    // No necesitamos los handles del proceso/hilo en este momento
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);

    // Envuelve hWrite (HANDLE) en un FILE* para usar fputs/fflush:
    int fd = _open_osfhandle((intptr_t)hWrite, _O_TEXT);
    if (fd == -1) {
        debug_log("rt_init", "_open_osfhandle failed");
        CloseHandle(hWrite);
        return NULL;
    }
    FILE* fp = _fdopen(fd, "w");
    if (!fp) {
        debug_log("rt_init", "_fdopen failed");
        _close(fd);
        return NULL;
    }
    return fp;
}
#endif

// ---------- init/shutdown ----------
void rt_init(void){
    if (g_py
#if defined(_WIN32)
        || g_sock != INVALID_SOCKET
#else
        || g_sock != -1
#endif
    ) return;

    // 0) Intentar modo EMBEBIDO por TCP (si app define TURTLE_TCP_ADDR=host:port)
    const char* tcp_env = getenv_safe("TURTLE_TCP_ADDR");
    if (tcp_env && tcp_env[0]) {
#if defined(_WIN32)
        WSADATA wsa; WSAStartup(MAKEWORD(2,2), &wsa);
        char host[256]={0}, port[64]={0};
        sscanf_s(tcp_env, "%255[^:]:%63s", host, (unsigned)_countof(host), port, (unsigned)_countof(port));
        free((void*)tcp_env);
        struct addrinfo hints; ZeroMemory(&hints,sizeof(hints));
        hints.ai_family = AF_UNSPEC; hints.ai_socktype = SOCK_STREAM;
        struct addrinfo* res = NULL;
        if (getaddrinfo(host, port, &hints, &res)==0) {
            SOCKET s = INVALID_SOCKET;
            for (struct addrinfo* p=res; p; p=p->ai_next){
                s = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
                if (s==INVALID_SOCKET) continue;
                if (connect(s, p->ai_addr, (int)p->ai_addrlen)==0){ g_sock = s; break; }
                closesocket(s);
            }
            freeaddrinfo(res);
        }
        if (g_sock != INVALID_SOCKET) { debug_log("rt_init","TCP connected (embed)"); return; }
#else
        char host[256]={0}, port[64]={0};
        sscanf(tcp_env, "%255[^:]:%63s", host, port);
        // getenv_safe devuelve puntero prestado en POSIX; no liberar
        struct addrinfo hints; memset(&hints,0,sizeof(hints));
        hints.ai_family = AF_UNSPEC; hints.ai_socktype = SOCK_STREAM;
        struct addrinfo* res = NULL;
        if (getaddrinfo(host, port, &hints, &res)==0) {
            int sfd = -1;
            for (struct addrinfo* p=res; p; p=p->ai_next){
                sfd = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
                if (sfd==-1) continue;
                if (connect(sfd, p->ai_addr, p->ai_addrlen)==0){ g_sock = sfd; break; }
                close(sfd);
            }
            freeaddrinfo(res);
        }
        if (g_sock != -1) { debug_log("rt_init","TCP connected (embed)"); return; }
#endif
        // si falla TCP, caemos al fallback (lanzar Python)
    }
#if defined(_WIN32)
    else { /* tcp_env era NULL */ }
#endif

    // 1) Preferido: TURTLE_PY_EXE + TURTLE_PY_SCRIPT
    const char* exe_raw = getenv_safe("TURTLE_PY_EXE");
    const char* scr_raw = getenv_safe("TURTLE_PY_SCRIPT");
#if defined(_WIN32)
    if (scr_raw && scr_raw[0]) {
        g_py = win_spawn_python((exe_raw && exe_raw[0]) ? exe_raw : NULL, scr_raw);
        if (exe_raw) free((void*)exe_raw);
        if (scr_raw) free((void*)scr_raw);
        if (g_py) return;
        debug_log("rt_init", "win_spawn_python failed (EXE+SCRIPT)");
    } else {
        if (exe_raw) free((void*)exe_raw);
        if (scr_raw) free((void*)scr_raw);
    }
#else
    if (exe_raw && exe_raw[0] && scr_raw && scr_raw[0]) {
        char cmd[4096];
        snprintf(cmd, sizeof(cmd), "\"%s\" -u \"%s\"", exe_raw, scr_raw);
        debug_log("rt_init", cmd);
        g_py = POPEN(cmd, "w");
        if (g_py) return;
        perror("[rt_init] popen (EXE+SCRIPT) failed");
    }
#endif

    // 2) Alternativa: comando completo TURTLE_PY_CMD (si alguien lo define)
    const char* override = getenv_safe("TURTLE_PY_CMD");
    if (override && override[0]) {
#if defined(_WIN32)
        // Podríamos parsear override; más simple: intentar CreateProcess con override directo como cmdline
        g_py = win_spawn_python(NULL, override); // esto no es ideal si trae flags; se recomienda EXE+SCRIPT
        free((void*)override);
        if (g_py) return;
        debug_log("rt_init", "win_spawn_python failed (override)");
#else
        debug_log("rt_init", override);
        g_py = POPEN(override, "w");
        free((void*)override);
        if (g_py) return;
        perror("[rt_init] popen (override) failed");
#endif
    }

    // 3) Fallback: buscar drawing.py junto al .exe y usar python launcher
#if defined(_WIN32)
    char exePath[MAX_PATH];
    DWORD n = GetModuleFileNameA(NULL, exePath, MAX_PATH);
    if (n > 0 && n < MAX_PATH) {
        char *last_sep = NULL;
        for (char *p = exePath; *p; ++p) if (*p=='\\' || *p=='/') last_sep = p;
        if (last_sep) *last_sep = '\0';
        char script_abs[MAX_PATH];
        snprintf(script_abs, sizeof(script_abs), "%s\\drawing.py", exePath);
        g_py = win_spawn_python(NULL, script_abs); // py.exe -u "...\drawing.py"
        if (!g_py) debug_log("rt_init", "fallback win_spawn_python failed");
    } else {
        debug_log("rt_init", "GetModuleFileNameA failed (fallback)");
    }
#else
    debug_log("rt_init", PY_CMD);
    g_py = POPEN(PY_CMD, "w");
    if (!g_py) perror("[rt_init] popen (PY_CMD) failed");
#endif
}

void rt_shutdown(void){
    // Primero, si estamos en TCP embed, cerrar socket
#if defined(_WIN32)
    if (g_sock != INVALID_SOCKET){
        send_cmd("QUIT");
        Sleep(50);
        closesocket(g_sock);
        g_sock = INVALID_SOCKET;
        WSACleanup();
        return;
    }
#else
    if (g_sock != -1){
        send_cmd("QUIT");
        usleep(50*1000);
        close(g_sock);
        g_sock = -1;
        return;
    }
#endif
    // Si no, cerrar proceso Python embebido
#if defined(_WIN32)
    if (g_py){ send_cmd("QUIT"); fclose(g_py); g_py = NULL; }
#else
    if (g_py){ send_cmd("QUIT"); PCLOSE(g_py); g_py = NULL; }
#endif
}

static int read_int_file(const char* path, int* out_val){
#if defined(_WIN32)
    FILE* f = NULL;
    if (fopen_s(&f, path, "rb") != 0 || !f) return 0;
    int v = 0;
    if (fscanf_s(f, "%d", &v) == 1) {
        fclose(f);
        *out_val = v;
        return 1;
    }
    fclose(f);
    return 0;
#else
    FILE* f = fopen(path, "rb");
    if (!f) return 0;
    int v = 0;
    if (fscanf(f, "%d", &v) == 1) {
        fclose(f);
        *out_val = v;
        return 1;
    }
    fclose(f);
    return 0;
#endif
}



// ---------- primitivas (enteros) ----------
void move_forward(int d){ char b[64]; snprintf(b,sizeof(b),"FORWARD %d", d); send_cmd(b); }
void move_backward(int d){ char b[64]; snprintf(b,sizeof(b),"BACK %d", d); send_cmd(b); }
void turn_right(int deg){ char b[64]; snprintf(b,sizeof(b),"RIGHT %d", deg); send_cmd(b); }
void turn_left(int deg){  char b[64]; snprintf(b,sizeof(b),"LEFT %d",  deg); send_cmd(b); }

void set_position(int x, int y){ char b[64]; snprintf(b,sizeof(b),"POS %d %d", x, y); send_cmd(b); }
void set_xy(int x, int y){        char b[64]; snprintf(b,sizeof(b),"POS %d %d", x, y); send_cmd(b); }
void set_x(int x){                char b[64]; snprintf(b,sizeof(b),"POSX %d", x); send_cmd(b); }
void set_y(int y){                char b[64]; snprintf(b,sizeof(b),"POSY %d", y); send_cmd(b); }
void set_heading(int h){          char b[64]; snprintf(b,sizeof(b),"HEADING %d", h); send_cmd(b); }
int get_heading(void){
#if defined(_WIN32)
    char dir[MAX_PATH], tmp[MAX_PATH];
    DWORD n = GetTempPathA(MAX_PATH, dir);
    if (n == 0 || n > MAX_PATH) return 0;
    if (GetTempFileNameA(dir, "tgh", 0, tmp) == 0) return 0;

    char cmd[512];
    snprintf(cmd, sizeof(cmd), "GETHEADING \"%s\"", tmp);
    send_cmd(cmd);

    DWORD waited = 0;
    const DWORD step_ms = 10, timeout_ms = 1000;
    while (waited < timeout_ms) {
        WIN32_FILE_ATTRIBUTE_DATA fad;
        if (GetFileAttributesExA(tmp, GetFileExInfoStandard, &fad)) {
            int val = 0;
            if (read_int_file(tmp, &val)) { DeleteFileA(tmp); return val; }
        }
        Sleep(step_ms);
        waited += step_ms;
    }
    DeleteFileA(tmp);
    return 0;
#else
    char tmp[] = "/tmp/tghXXXXXX";
    int fd = mkstemp(tmp);
    if (fd == -1) return 0;
    close(fd);

    char cmd[512];
    snprintf(cmd, sizeof(cmd), "GETHEADING \"%s\"", tmp);
    send_cmd(cmd);

    int waited = 0;
    const int step_ms = 10, timeout_ms = 1000;
    while (waited < timeout_ms) {
        int val = 0;
        if (read_int_file(tmp, &val)) { remove(tmp); return val; }
        usleep(step_ms * 1000);
        waited += step_ms;
    }
    remove(tmp);
    return 0;
#endif
}

void pen_up(void){ send_cmd("PENUP"); }
void pen_down(void){ send_cmd("PENDOWN"); }
void hide_turtle(void){ send_cmd("HIDE"); }
void set_color(int c){ char b[64]; snprintf(b,sizeof(b),"COLOR %d", c); send_cmd(b); }
void sleep_ms(int ms){ sleep_ms_os(ms); }
void delay_ms(int ms){
    char b[64];
    snprintf(b, sizeof(b), "DELAY %d", ms);
    send_cmd(b);
}
int rand_int(int maxv){
#if defined(_WIN32)
    if (maxv <= 0) return 0;
    char dir[MAX_PATH], tmp[MAX_PATH];
    DWORD n = GetTempPathA(MAX_PATH, dir);
    if (n == 0 || n > MAX_PATH) return 0;
    if (GetTempFileNameA(dir, "rnd", 0, tmp) == 0) return 0;

    char cmd[512];
    snprintf(cmd, sizeof(cmd), "RANDINT %d \"%s\"", maxv, tmp);
    send_cmd(cmd);

    DWORD waited = 0;
    const DWORD step_ms = 10, timeout_ms = 1000;
    while (waited < timeout_ms) {
        WIN32_FILE_ATTRIBUTE_DATA fad;
        if (GetFileAttributesExA(tmp, GetFileExInfoStandard, &fad)) {
            int val = 0;
            if (read_int_file(tmp, &val)) { DeleteFileA(tmp); return val; }
        }
        Sleep(step_ms);
        waited += step_ms;
    }
    DeleteFileA(tmp);
    return 0;
#else
    if (maxv <= 0) return 0;
    char tmp[] = "/tmp/rndXXXXXX";
    int fd = mkstemp(tmp);
    if (fd == -1) return 0;
    close(fd);

    char cmd[512];
    snprintf(cmd, sizeof(cmd), "RANDINT %d \"%s\"", maxv, tmp);
    send_cmd(cmd);

    int waited = 0;
    const int step_ms = 10, timeout_ms = 1000;
    while (waited < timeout_ms) {
        int val = 0;
        if (read_int_file(tmp, &val)) { remove(tmp); return val; }
        usleep(step_ms * 1000);
        waited += step_ms;
    }
    remove(tmp);
    return 0;
#endif
}

void center_turtle(void){ send_cmd("CENTER"); }

// ---------- utilidad ----------
int pow_int(int a, int b){
#if defined(_WIN32)
    char dir[MAX_PATH], tmp[MAX_PATH];
    DWORD n = GetTempPathA(MAX_PATH, dir);
    if (n == 0 || n > MAX_PATH) return 0;
    if (GetTempFileNameA(dir, "pow", 0, tmp) == 0) return 0;

    char cmd[512];
    snprintf(cmd, sizeof(cmd), "POWINT %d %d \"%s\"", a, b, tmp);
    send_cmd(cmd);

    DWORD waited = 0;
    const DWORD step_ms = 10, timeout_ms = 1000;
    while (waited < timeout_ms) {
        WIN32_FILE_ATTRIBUTE_DATA fad;
        if (GetFileAttributesExA(tmp, GetFileExInfoStandard, &fad)) {
            int val = 0;
            if (read_int_file(tmp, &val)) { DeleteFileA(tmp); return val; }
        }
        Sleep(step_ms);
        waited += step_ms;
    }
    DeleteFileA(tmp);
    return 0;
#else
    char tmp[] = "/tmp/powXXXXXX";
    int fd = mkstemp(tmp);
    if (fd == -1) return 0;
    close(fd);

    char cmd[512];
    snprintf(cmd, sizeof(cmd), "POWINT %d %d \"%s\"", a, b, tmp);
    send_cmd(cmd);

    int waited = 0;
    const int step_ms = 10, timeout_ms = 1000;
    while (waited < timeout_ms) {
        int val = 0;
        if (read_int_file(tmp, &val)) { remove(tmp); return val; }
        usleep(step_ms * 1000);
        waited += step_ms;
    }
    remove(tmp);
    return 0;
#endif
}
