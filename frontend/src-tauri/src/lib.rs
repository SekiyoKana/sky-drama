use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandEvent;
use tauri::Emitter;
use std::env;
use std::fs::OpenOptions;
use std::io::Write;
use std::path::PathBuf;

// 辅助函数：将日志写入文件
fn write_log(msg: String) {
    // 获取当前 exe 所在目录
    let log_path = if let Ok(current_exe) = env::current_exe() {
        if let Some(parent) = current_exe.parent() {
            parent.join("_sidecar_debug.log")
        } else {
            PathBuf::from("_sidecar_debug.log")
        }
    } else {
        PathBuf::from("_sidecar_debug.log")
    };

    // 追加写入模式打开文件
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_path) {
        let _ = writeln!(file, "{}", msg);
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .plugin(tauri_plugin_fs::init())
    .plugin(tauri_plugin_dialog::init())
    .setup(|app| {
      // 为了调试，暂时移除 !cfg!(debug_assertions) 判断，或者你可以保留它但确保自己在运行 release 包
      // 这里我保留你的逻辑，只在生产环境生效
      if !cfg!(debug_assertions) {
          write_log("Starting Sidecar Sequence...".to_string());
          
          let sidecar = app.shell().sidecar("backend_api");
          
          match sidecar {
              Ok(mut cmd) => {
                  let mut work_dir_path = String::new();

                  // macOS logic
                  #[cfg(target_os = "macos")]
                  {
                      if let Some(home_dir) = dirs::home_dir() {
                          let app_data_dir = home_dir.join("Library/Application Support/com.sekiyo.skydrama");
                          let _ = std::fs::create_dir_all(&app_data_dir);
                          work_dir_path = app_data_dir.to_string_lossy().to_string();
                      }
                  }

                  // Windows/Linux logic
                  #[cfg(not(target_os = "macos"))]
                  {
                      if let Ok(current_exe) = env::current_exe() {
                          if let Some(parent) = current_exe.parent() {
                              work_dir_path = parent.to_string_lossy().to_string();
                          }
                      }
                  }
                  
                  write_log(format!("Work Dir Detected: {}", work_dir_path));

                  // 注入环境变量
                  if !work_dir_path.is_empty() {
                      cmd = cmd.env("APP_WORK_DIR", &work_dir_path);
                      #[cfg(target_os = "macos")]
                      {
                          cmd = cmd.env("DYLD_LIBRARY_PATH", &work_dir_path);
                      }
                  }

                  match cmd.spawn() {
                      Ok((mut rx, _child)) => {
                          write_log("Sidecar spawned successfully.".to_string());
                          let app_handle = app.handle().clone();
                          
                          tauri::async_runtime::spawn(async move {
                              while let Some(event) = rx.recv().await {
                                  match event {
                                      CommandEvent::Stdout(line) => {
                                          let msg = String::from_utf8_lossy(&line).to_string();
                                          // 1. 发给前端
                                          let _ = app_handle.emit("backend-log", format!("[INFO] {}", msg));
                                          // 2. 写入文件
                                          write_log(format!("[STDOUT] {}", msg));
                                      }
                                      CommandEvent::Stderr(line) => {
                                          let msg = String::from_utf8_lossy(&line).to_string();
                                          // 1. 发给前端
                                          let _ = app_handle.emit("backend-log", format!("[ERR] {}", msg));
                                          // 2. 写入文件
                                          write_log(format!("[STDERR] {}", msg));
                                      }
                                      _ => {}
                                  }
                              }
                              write_log("Sidecar process terminated.".to_string());
                          });
                      }
                      Err(e) => {
                          let err_msg = format!("Failed to spawn sidecar: {}", e);
                          eprintln!("{}", err_msg);
                          write_log(err_msg);
                      },
                  }
              }
              Err(e) => {
                  let err_msg = format!("Failed to create sidecar command: {}", e);
                  eprintln!("{}", err_msg);
                  write_log(err_msg);
              },
          }
      } else {
          println!("[DEV MODE] Skipping sidecar spawn.");
      }
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}