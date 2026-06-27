// Star Alliance — Mission Console desktop shell.
// On launch it spawns the dashboard server (the real repo's .claude/serve.cjs) as a
// bundled-node sidecar, waits for the port, then reveals the window pointed at it.
// The sidecar runs against the REAL repo on disk so edits write through to source —
// the whole point of the control panel. The sidecar is killed when the app quits.
#![cfg_attr(all(not(debug_assertions), target_os = "windows"), windows_subsystem = "windows")]

use std::net::TcpStream;
use std::sync::Mutex;
use std::time::{Duration, Instant};

use tauri::{Manager, WindowEvent};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

const PORT: u16 = 4178;
// Default repo root; override with STAR_ALLIANCE_ROOT. This app edits the live repo
// on this machine, so it must point at the real working copy — not a bundled snapshot.
const DEFAULT_ROOT: &str = "/Users/attaselim/Documents/Claude/Projects/star-alliance";

fn repo_root() -> String {
    std::env::var("STAR_ALLIANCE_ROOT").unwrap_or_else(|_| DEFAULT_ROOT.to_string())
}

fn port_is_up() -> bool {
    TcpStream::connect_timeout(
        &format!("127.0.0.1:{PORT}").parse().unwrap(),
        Duration::from_millis(400),
    )
    .is_ok()
}

// Hold the sidecar child so we can kill it on quit.
struct Sidecar(Mutex<Option<CommandChild>>);

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(Sidecar(Mutex::new(None)))
        .setup(|app| {
            let root = repo_root();
            let serve = format!("{root}/.claude/serve.cjs");

            // Spawn the dashboard server as the bundled-node sidecar, cwd = repo.
            let (_rx, child) = app
                .shell()
                .sidecar("node")
                .expect("node sidecar missing")
                .args([serve.as_str()])
                .current_dir(std::path::PathBuf::from(&root))
                .spawn()
                .expect("failed to spawn dashboard server");
            app.state::<Sidecar>().0.lock().unwrap().replace(child);

            // Wait for the server to answer, then reveal the window.
            let deadline = Instant::now() + Duration::from_secs(15);
            while Instant::now() < deadline && !port_is_up() {
                std::thread::sleep(Duration::from_millis(250));
            }
            if let Some(win) = app.get_webview_window("main") {
                let _ = win.show();
                let _ = win.set_focus();
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            // Kill the sidecar when the main window closes.
            if let WindowEvent::Destroyed = event {
                if let Some(child) = window.state::<Sidecar>().0.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Star Alliance");
}
