/*
 * Silent deaths on Switch: abort(), exit() and whatever goes to stderr.
 *
 * newlib's abort() returns to the HOME menu without a word (measured on the first
 * boot of the SDK, see switch_libc_supplement.c). rex::FatalError ends there, as do
 * std::terminate (an uncaught exception, a std::thread destroyed without join) and
 * Mesa's aborts. And they all warn on stderr first, which goes nowhere in an NRO.
 *
 * It has to be in the executable, in rexglue_switch_startup, and not in a library:
 * the definition of abort has to reach the link before the one in libc.a to
 * replace it.
 *
 *   stderr  -> <NRO folder>/logs/rex/rex_stderr.log, unbuffered, rewritten on every boot; the previous run's is
 *              kept as rex_stderr_previous.log (the open one cannot be read while the game runs, see
 *              core/copyable_file_sink.h)
 *   abort() -> <NRO folder>/logs/rex/rex_crash.log with the stack, and error 2345-0101
 *   exit()  -> the same, error 2345-0103. The orderly shutdown does not go through exit()
 *              (see windowed_app_main_switch.cpp), so getting here means some library
 *              decided to end the process on its own.
 *
 * The rexglue logs go to <NRO folder>/logs/rex/ and not to sdmc:/switch/, so they do not mix with
 * those of other programs or with the game's, which go to <NRO folder>/logs/. The folder comes from
 * argv[0], which libnx fills in before the constructors. Without argv[0], sdmc:/switch/ is used.
 */

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#include <switch.h>

/* Filled in by libnx (argv.c), which does not declare them in its headers. */
extern int __system_argc;
extern char** __system_argv;

/* Ends in '/'. Computed once at startup and never changes: the fault handler reads it without allocating memory. */
static char g_rex_log_dir[FS_MAX_PATH] = "sdmc:/switch/";

const char* RexSwitchLogDir(void) {
    return g_rex_log_dir;
}

static void RexSwitchInitLogDir(void) {
    if (__system_argc < 1 || !__system_argv || !__system_argv[0]) {
        return;
    }
    const char* nro = __system_argv[0];
    const char* slash = strrchr(nro, '/');
    if (!slash) {
        return;
    }
    /* without a device ("/switch/..."), the SD one: the path must also work for fsdevTranslatePath */
    const char* device = strchr(nro, ':') ? "" : "sdmc:";
    char dir[FS_MAX_PATH];
    int n = snprintf(dir, sizeof(dir), "%s%.*slogs", device, (int)(slash - nro + 1), nro);
    if (n <= 0 || (size_t)n + sizeof("/rex/") > sizeof(dir)) {
        return;
    }
    mkdir(dir, 0777);
    strcat(dir, "/rex");
    mkdir(dir, 0777);
    struct stat st;
    if (stat(dir, &st) == 0 && S_ISDIR(st.st_mode)) {
        strcat(dir, "/");
        strcpy(g_rex_log_dir, dir);
    }
}

void RexSwitchCrashLog(const char* reason, const ThreadExceptionDump* ctx, u64 stack, u64 pc);

/*
 * Test consoles left to run on their own: with RexSwitchSetRestartOnCrash(true) a crash, once its report is written,
 * asks the system to restart the application (appletRestartProgram) instead of stopping on the error screen, so an
 * unattended test loop goes on and the next start sends the report. Off by default: players get the error screen.
 * If the system refuses (a start under hbmenu's title takeover) or has not ended the process within 10 s, the error
 * screen comes up as usual.
 */
static volatile bool g_rex_restart_on_crash = false;
static char g_rex_restart_marker[FS_MAX_PATH] = "";

void RexSwitchSetRestartOnCrash(bool on) { g_rex_restart_on_crash = on; }

/* Optional application-owned recovery marker. An empty path keeps the existing restart behavior. */
bool RexSwitchSetCrashRestartMarker(const char* path) {
    if (!path) {
        g_rex_restart_marker[0] = '\0';
        return true;
    }
    const size_t size = strnlen(path, sizeof(g_rex_restart_marker));
    if (size >= sizeof(g_rex_restart_marker)) return false;
    memcpy(g_rex_restart_marker, path, size + 1);
    return true;
}

NX_NORETURN void RexSwitchCrashEnd(Result result) {
    bool restart = g_rex_restart_on_crash;
    if (restart && g_rex_restart_marker[0]) {
        /* The report is already closed. If recovery cannot be recorded, keep the error visible. */
        FILE* marker = fopen(g_rex_restart_marker, "wb");
        if (!marker) {
            restart = false;
        } else {
            const bool written = fputs("main fatal restart\n", marker) >= 0;
            const bool closed = fclose(marker) == 0;
            restart = written && closed;
        }
    }
    if (restart && R_SUCCEEDED(appletRestartProgram(NULL, 0))) {
        for (int i = 0; i < 40; ++i) {
            svcSleepThread(250000000LL);
        }
    }
    diagAbortWithResult(result);
}

void abort(void) {
    RexSwitchCrashLog("abort()", NULL, (u64)__builtin_frame_address(0),
                      (u64)__builtin_return_address(0));
    RexSwitchCrashEnd(MAKERESULT(Module_Libnx, 101));
}

static void RexSwitchExitHook(void) {
    RexSwitchCrashLog("exit() outside the orderly shutdown", NULL, (u64)__builtin_frame_address(0),
                      (u64)__builtin_return_address(0));
    RexSwitchCrashEnd(MAKERESULT(Module_Libnx, 103));
}

/*
 * Priority 101, the first one allowed: before any static constructor of the
 * SDK, which can also die. The SD is already mounted: __appInit runs before the
 * constructors.
 */
__attribute__((constructor(101)))
static void RexSwitchCrashHooksInit(void) {
    RexSwitchInitLogDir();
    char path_str[FS_MAX_PATH];
    snprintf(path_str, sizeof(path_str), "%srex_stderr.log", g_rex_log_dir);
    char previous[FS_MAX_PATH];
    snprintf(previous, sizeof(previous), "%srex_stderr_previous.log", g_rex_log_dir);
    remove(previous);
    rename(path_str, previous);
    if (freopen(path_str, "w", stderr)) {
        setvbuf(stderr, NULL, _IONBF, 0);
    }
    atexit(RexSwitchExitHook);
}
